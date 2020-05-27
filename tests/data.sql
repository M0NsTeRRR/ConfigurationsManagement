INSERT INTO user (login, password, gitea_token, api_key)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f', NULL, 'API_KEY');

INSERT INTO task (hostname, module, action, path, state, error, message, start_date, end_date)
VALUES
  ('pfsense.test', 'pfsense', 'save', '/pfsense/backup12.zip', '3', '1', 'Error', '2020-05-10 22:24:12.104606+00:00', '2020-05-10 22:24:12.104606+00:00'),
  ('192.168.0.1', 'pfsense', 'restore', '/pfsense/backup12.zip', '4', '0', NULL, '2020-05-10 22:24:12.104606+00:00', '2020-05-10 22:24:12.104606+00:00'),
  ('192.168.0.1', 'pfsense', 'save', '/pfsense/backup12.zip', '4', '0', NULL, '2020-05-10 22:24:12.104606+00:00', '2020-05-10 22:24:12.104606+00:00'),
  ('192.168.0.1', 'pfsense', 'save', '/pfsense/backup12.zip', '3', '0', NULL, '2020-05-10 22:24:12.104606+00:00', NULL),
  ('192.168.0.1', 'pfsense', 'save', '/pfsense/backup12.zip', '2', '0', NULL, '2020-05-10 22:24:12.104606+00:00', NULL),
  ('192.168.0.1', 'pfsense', 'save', '/pfsense/backup12.zip', '1', '0', NULL, '2020-05-10 22:24:12.104606+00:00', NULL);