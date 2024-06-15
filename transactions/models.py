from django.db import models


class TransactionCategory(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.category


class TransactionSubCategory(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(TransactionCategory, on_delete=models.SET_NULL, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name


class IncomeCategory(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.category


class PaymentMethod(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=False)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name


class Income(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(IncomeCategory, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    destination = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(default=None, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.amount) + " " + str(self.date)


class Transaction(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(TransactionCategory, on_delete=models.SET_NULL, null=True, blank=True)
    subcategory = models.ForeignKey(TransactionSubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    destination_original = models.CharField(max_length=255, blank=True, null=True)
    destination = models.CharField(max_length=255, blank=True, null=True)
    alias = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(default=None, blank=True, null=True)
    is_saving = models.BooleanField(default=False)
    is_payment = models.BooleanField(default=False)
    is_expense = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_merge = models.BooleanField(default=False)
    merge_id = models.IntegerField(default=None, blank=True, null=True)
    delete_reason = models.TextField(default=None, blank=True, null=True)
    source = models.IntegerField(default=0, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.amount) + " " + str(self.date)


class DestinationMap(models.Model):
    id = models.AutoField(primary_key=True)
    destination = models.CharField(max_length=255, blank=True, null=True)
    destination_original = models.CharField(max_length=255, blank=True, null=True)
    destination_eng = models.CharField(max_length=255, blank=True, null=True)
    keywords = models.TextField(blank=True, null=True)
    category = models.ForeignKey(TransactionCategory, on_delete=models.SET_NULL, null=True, blank=True)
    subcategory = models.ForeignKey(TransactionSubCategory, on_delete=models.SET_NULL, null=True, blank=True)


class ImportRules(models.Model):
    id = models.AutoField(primary_key=True)
    source = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    last_import_date = models.DateField(blank=True, null=True)
