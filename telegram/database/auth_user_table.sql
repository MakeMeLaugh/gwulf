CREATE TABLE `telegram_bot`.auth_users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `chat_id` int(11) NOT NULL COMMENT 'Chat id',
  `approved` tinyint(1) DEFAULT '0' COMMENT '0 - user can not receive messages from bot; 1 - user can receive messages from bot',
  PRIMARY KEY (`id`),
  UNIQUE KEY `UIX_chat_id` (`chat_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin