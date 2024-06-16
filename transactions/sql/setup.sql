insert into personal_finance.transactions_incomecategory (id, category)
values  (1, 'Salary/Wages'),
        (2, 'Freelance Income'),
        (3, 'Investment Income'),
        (4, 'Rental Income'),
        (5, 'Side Gig Income'),
        (6, 'Interest Income'),
        (7, 'Bonus/Commission'),
        (8, 'Gifts/Donations'),
        (9, 'Government Assistance'),
        (10, 'Other');

insert into personal_finance.transactions_paymentmethod (id, name, description)
values  (1, 'Rakuten Card', null),
        (2, 'EPOS Card', null),
        (3, 'Docomo Card', null),
        (4, 'Cash', null);

insert into personal_finance.transactions_transactioncategory (id, category)
values  (1, 'Housing'),
        (2, 'Transportation'),
        (3, 'Food'),
        (4, 'Utilities'),
        (5, 'Taxes'),
        (6, 'Savings'),
        (7, 'Entertainment'),
        (8, 'Shopping'),
        (9, 'Clothing and Accessories'),
        (10, 'Personal Care'),
        (11, 'Healthcare'),
        (12, 'Insurance'),
        (13, 'Education'),
        (14, 'Cash Payments'),
        (15, 'Charitable Giving'),
        (16, 'Miscellaneous'),
        (1000, 'N/A');

insert into personal_finance.transactions_transactionsubcategory (id, name, description, category_id)
values  (1, 'Mortgage/Rent', null, 1),
        (2, 'Home/Parking Management fees', null, 1),
        (3, 'Home Insurance', null, 1),
        (4, 'Home Repairs/Maintenance', null, 1),
        (5, 'Car Payment', null, 2),
        (6, 'Auto Insurance', null, 2),
        (7, 'Fuel/Gas', null, 2),
        (8, 'Maintenance/Repairs', null, 2),
        (9, 'Public Transportation', null, 2),
        (10, 'Parking', null, 2),
        (11, 'Tolls', null, 2),
        (12, 'Car Rental', null, 2),
        (13, 'Groceries', null, 3),
        (14, 'Dining Out', null, 3),
        (15, 'Snacks/Coffee', null, 3),
        (16, 'Electricity', null, 4),
        (17, 'Gas', null, 4),
        (18, 'Water', null, 4),
        (19, 'Internet', null, 4),
        (20, 'Phone/Mobile', null, 4),
        (21, 'Cable/TV', null, 4),
        (22, 'Income Tax', null, 5),
        (23, 'Residence Tax', null, 5),
        (24, 'Property Tax', null, 5),
        (25, 'Vehicle Tax', null, 5),
        (26, 'Other', null, 5),
        (27, 'Emergency Fund', null, 6),
        (28, 'Investments (Securities)', null, 6),
        (29, 'Retirement Savings', null, 6),
        (30, 'Cash Deposits', null, 6),
        (31, 'Subscriptions', null, 7),
        (32, 'Movies/Theater/Concerts', null, 7),
        (33, 'Entrance Tickets', null, 7),
        (34, 'Hobbies', null, 7),
        (35, 'Vacations/Travel', null, 7),
        (36, 'Household Items', null, 8),
        (37, 'Furniture', null, 8),
        (38, 'Electronics', null, 8),
        (39, 'Miscellaneous', null, 8),
        (40, 'Clothing Purchases', null, 9),
        (41, 'Shoes Purchases', null, 9),
        (42, 'Dry Cleaning/Laundry', null, 9),
        (43, 'Haircuts/Salon', null, 10),
        (44, 'Cosmetics/Toiletries', null, 10),
        (45, 'Gym Memberships', null, 10),
        (46, 'Health Insurance Premiums', null, 11),
        (47, 'Medical/Dental/Vision Expenses', null, 11),
        (48, 'Prescriptions/Medications', null, 11),
        (49, 'Health Club Memberships', null, 11),
        (50, 'Life Insurance', null, 12),
        (51, 'Disability Insurance', null, 12),
        (52, 'Long-Term Care Insurance', null, 12),
        (53, 'Educational Courses', null, 13),
        (54, 'Tuition/Fees', null, 13),
        (55, 'Books/Supplies', null, 13),
        (56, 'Personal Loan Payments', null, 14),
        (57, 'Credit Card Payments', null, 14),
        (58, 'Cash Payments', null, 14),
        (59, 'Donations to Charities/Organizations', null, 15),
        (60, 'Gifts', null, 16),
        (61, 'Pet Expenses', null, 16),
        (62, 'Bank Fees', null, 16),
        (63, 'Postal Fees', null, 16),
        (64, 'Legal/Professional Fees', null, 16),
        (1000, 'N/A', null, 1000);

# INSERT INTO personal_finance.transactions_rewriterules (destination, keywords)
# VALUES
#     ('Softbank', 'ソフトバンク'),
#     ('Spotify', 'SPOTIFY'),
#     ('SevenEleven', 'セブン－イレブン,セブンイレブン'),
#     ('Lawson', 'ロ―ソン,ローソン,ロ－ソン'),
#     ('Family Mart', 'フアミリ―マ―ト,ファミリーマート'),
#     ('Toyota Rent a Car', 'トヨタレンタリース,ﾄﾖﾀﾚﾝﾀﾘｰｽ'),
#     ('MEGA Donqui', 'ＭＥＧＡドン・キ,メガドンキ'),
#     ('Starbucks', 'ｽﾀ-ﾊﾞﾂｸｽ,スタ－バツクス,スターバックス'),
#     ('Daiso', 'ダイソー,ＤＡＩＳＯ,ダイソ－'),
#     ('Seria', 'セリア'),
#     ('Gyomu Super', 'ギヨウムス－パ－,業務ス－パ－,ｷﾞﾖｳﾑｽ-ﾊﾟ-'),
#     ('HAC Drug Store', 'ハツクドラツグ,ハックドラッグ'),
#     ('Uber Eats', 'UBER *EATS,ＵＢＥＲ　ＥＡＴＳ,UBER   *EATS,UBER * EATS'),
#     ('Uber Pass', 'UBER *PASS,UBER *ONE'),
#     ('ATM Withdrawal', 'ＡＴＭ'),
#     ('Cash Payments', 'ＪＣＢデビット'),
#     ('Second Street', 'セカンドストリート'),
#     ('TOKYU SC', 'クトウキユウ　エスシ－'),
#     ('CREATE', 'クリエイト　エス・ディーアプリ,クリエイトエスデイ－,クリエイト,ｸﾘｴｲﾄ'),
#     ('Appolo Station', 'イデミツ（アポロステーション,アポロステ－シヨン,イデミツ（アポロ／シェル'),
#     ('PASMO', 'モバイルＰＡＳＭＯチャージ,モバイルパスモチヤ－ジ'),
#     ('CONAN', 'ホームセンターコーナン　アプリ,コ－ナン商事,コ－ナン　コウホクセンタ－ミナミテン'),
#     ('Netflix', 'ＮＥＴＦＬＩＸ．ＣＯＭ,ネツトフリツクス'),
#     ('ETC', 'ＥＴＣ'),
#     ('McDonald''s', 'マクドナルド'),
#     ('HardOff', 'オフハウス'),
#     ('Yokohama Waterworks Bureau', 'ヨコハマスイドウ');
