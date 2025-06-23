import copy

from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from django.forms import model_to_dict

from changelog.models import ChangeLog, ActionEnum
from changelog.signals import log_change
from oauth.middleware import get_current_user

EXCLUDED_MODELS = {'ChangeLog'}

def get_changes(old_instance, new_instance):
    old_data = model_to_dict(old_instance)
    new_data = model_to_dict(new_instance)
    return prepare_json_fields(new_data, old_data)

def prepare_json_fields(new_data, old_data):
    return {
        field: {'old': str(old_data.get(field)) if old_data else None, 'new': str(new_data.get(field))}
        for field in new_data
        if old_data.get(field) != new_data.get(field)
    }


@receiver(log_change)
def log_change(sender, **kwargs):
    if sender.__name__ in EXCLUDED_MODELS:
        return
    action = kwargs.get('action')
    section = kwargs.get('section')
    if action == ActionEnum.CREATE:
        instance = kwargs.get('instance')
        change_dict = model_to_dict(instance)
        changes = prepare_json_fields(change_dict, {})
        save_changes(changes, action, section, instance)
    elif action == ActionEnum.UPDATE:
        instance = kwargs.get('instance')
        old = kwargs.get('old_instance')
        changes = get_changes(old, instance)
        if 'is_deleted' in changes:
            new_value = changes['is_deleted'].get('new')
            old_value = changes['is_deleted'].get('old')
            if new_value != old_value and new_value == 'True':
                action = ActionEnum.DELETE
        save_changes(changes, action, section, instance)
    elif action == ActionEnum.BULK_DELETE:
        changed_objects = kwargs['instances']
        for changed_object in changed_objects:
            instance = copy.deepcopy(changed_object)
            changed_object.is_deleted = True
            changed_object.delete_reason = kwargs.get('delete_reason', '')
            changes = get_changes(instance, changed_object)
            save_changes(changes, action, section, instance)
    elif action == ActionEnum.MERGE:
        merged_objects = kwargs['instances']
        merged_to = kwargs['merged_to']
        for merged_object in merged_objects:
            instance = copy.deepcopy(merged_object)
            merged_object.is_merge = True
            merged_object.merge_id = merged_to
            changes = get_changes(instance, merged_object)
            save_changes(changes, action, section, instance)



def save_changes(changes, action, section, instance):
    if changes:
        ChangeLog.objects.create(
            content_type=ContentType.objects.get_for_model(instance.__class__),
            object_id=str(instance.pk),
            section=section,
            action=action,
            changelog=changes,
            user=get_current_user()
        )
