CREATE TABLE `msg_updates` (
  `update_id` bigint(20) NOT NULL COMMENT 'Last handled update_id',
  PRIMARY KEY (`update_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8
;