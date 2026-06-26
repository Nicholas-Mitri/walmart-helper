
-- Mock data for picks table
INSERT INTO picks (product_id, quantity) VALUES
  (11, 3),
  (22, 1),
  (31, 2),
  (63, 1),
  (27, 5);

-- Mock data for activity_log table
-- Valid ENUM(actions): 'throw', 'cvp', 'vizpik', 'restock', 'clean_daily', 'clean_pm', 'temp_check', 'general_note', 'product_note', 'donate', 'floor_sweep', 'recovery'
INSERT INTO activity_log (product_id, action, cases_qty, units_qty, notes) VALUES
  (1, 'restock', NULL, 3, 'User 1 restocked product 1'),
  (2, 'vizpik', 1, NULL, 'Vizpik for product 2'),
  (3, 'vizpik', 2, NULL, NULL),
  (NULL, 'clean_daily', NULL, NULL, 'User 3 did daily cleaning'),
  (2, 'donate', NULL, 2, 'Product 2 was donated'),
  (NULL, 'recovery', NULL, 3, 'Recovery check by supervisor on pick'),
  (NULL, 'general_note', NULL, NULL, 'User 1 left a general note');

select * from picks;

select * from activity_log;