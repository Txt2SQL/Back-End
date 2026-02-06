CREATE TABLE `accounts_customuser`(
    `password` VARCHAR(255) NOT NULL,
    `last_login` DATETIME NULL,
    `is_superuser` TINYINT NOT NULL,
    `username` VARCHAR(255) NOT NULL,
    `first_name` VARCHAR(255) NOT NULL,
    `last_name` VARCHAR(255) NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `is_staff` TINYINT NOT NULL,
    `is_active` TINYINT NOT NULL,
    `date_joined` DATETIME NOT NULL,
    `id` CHAR(255) NOT NULL,
    `karma` INT NOT NULL,
    `about` LONGTEXT NOT NULL,
    `level` INT NOT NULL,
    `lft` INT NOT NULL,
    `parent_id` CHAR(255) NULL,
    `rght` INT NOT NULL,
    `tree_id` INT NOT NULL,
    `used_invitation_id` CHAR(255) NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `accounts_customuser` ADD UNIQUE `accounts_customuser_username_unique`(`username`);
ALTER TABLE
    `accounts_customuser` ADD INDEX `accounts_customuser_parent_id_index`(`parent_id`);
ALTER TABLE
    `accounts_customuser` ADD INDEX `accounts_customuser_tree_id_index`(`tree_id`);
ALTER TABLE
    `accounts_customuser` ADD INDEX `accounts_customuser_used_invitation_id_index`(`used_invitation_id`);
CREATE TABLE `accounts_customuser_groups`(
    `id` INT NOT NULL,
    `customuser_id` CHAR(255) NOT NULL,
    `group_id` INT NOT NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `accounts_customuser_groups` ADD UNIQUE `accounts_customuser_groups_customuser_id_group_id_unique`(`customuser_id`, `group_id`);
ALTER TABLE
    `accounts_customuser_groups` ADD INDEX `accounts_customuser_groups_group_id_index`(`group_id`);
CREATE TABLE `accounts_customuser_user_permissions`(
    `id` INT NOT NULL,
    `customuser_id` CHAR(255) NOT NULL,
    `permission_id` INT NOT NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `accounts_customuser_user_permissions` ADD UNIQUE `customuser_id_permission_id_unique`(`customuser_id`, `permission_id`);
ALTER TABLE
    `accounts_customuser_user_permissions` ADD INDEX `accounts_customuser_user_permissions_permission_id_index`(`permission_id`);
CREATE TABLE `accounts_emailverification`(
    `id` CHAR(255) NOT NULL,
    `created_at` DATETIME NOT NULL,
    `changed_at` DATETIME NOT NULL,
    `verified` TINYINT NOT NULL,
    `verified_at` DATETIME NULL,
    `email` VARCHAR(255) NOT NULL,
    `user_id` CHAR(255) NOT NULL,
    `verification_code` CHAR(255) NOT NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `accounts_emailverification` ADD INDEX `accounts_emailverification_user_id_index`(`user_id`);
CREATE TABLE `accounts_invitation`(
    `id` CHAR(255) NOT NULL,
    `created_at` DATETIME NOT NULL,
    `changed_at` DATETIME NOT NULL,
    `num_signups` INT NULL,
    `invited_email_address` VARCHAR(255) NULL,
    `invite_code` CHAR(255) NOT NULL,
    `inviting_user_id` CHAR(255) NOT NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `accounts_invitation` ADD INDEX `accounts_invitation_inviting_user_id_index`(`inviting_user_id`);
CREATE TABLE `accounts_passwordresetrequest`(
    `id` CHAR(255) NOT NULL,
    `created_at` DATETIME NOT NULL,
    `changed_at` DATETIME NOT NULL,
    `verification_code` CHAR(255) NOT NULL,
    `user_id` CHAR(255) NOT NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `accounts_passwordresetrequest` ADD INDEX `accounts_passwordresetrequest_user_id_index`(`user_id`);
CREATE TABLE `auth_group`(
    `id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `auth_group` ADD UNIQUE `auth_group_name_unique`(`name`);
CREATE TABLE `auth_group_permissions`(
    `id` INT NOT NULL,
    `group_id` INT NOT NULL,
    `permission_id` INT NOT NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `auth_group_permissions` ADD UNIQUE `auth_group_permissions_group_id_permission_id_unique`(`group_id`, `permission_id`);
ALTER TABLE
    `auth_group_permissions` ADD INDEX `auth_group_permissions_permission_id_index`(`permission_id`);
CREATE TABLE `auth_permission`(
    `id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `content_type_id` INT NOT NULL,
    `codename` VARCHAR(255) NOT NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `auth_permission` ADD UNIQUE `auth_permission_content_type_id_codename_unique`(`content_type_id`, `codename`);
CREATE TABLE `django_admin_log`(
    `id` INT NOT NULL,
    `action_time` DATETIME NOT NULL,
    `object_id` LONGTEXT NULL,
    `object_repr` VARCHAR(255) NOT NULL,
    `action_flag` SMALLINT NOT NULL,
    `change_message` LONGTEXT NOT NULL,
    `content_type_id` INT NULL,
    `user_id` CHAR(255) NOT NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `django_admin_log` ADD INDEX `django_admin_log_content_type_id_index`(`content_type_id`);
ALTER TABLE
    `django_admin_log` ADD INDEX `django_admin_log_user_id_index`(`user_id`);
CREATE TABLE `django_content_type`(
    `id` INT NOT NULL,
    `app_label` VARCHAR(255) NOT NULL,
    `model` VARCHAR(255) NOT NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `django_content_type` ADD UNIQUE `django_content_type_app_label_model_unique`(`app_label`, `model`);
CREATE TABLE `django_migrations`(
    `id` INT NOT NULL,
    `app` VARCHAR(255) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `applied` DATETIME NOT NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `django_session`(
    `session_key` VARCHAR(255) NOT NULL,
    `session_data` LONGTEXT NOT NULL,
    `expire_date` DATETIME NOT NULL,
    PRIMARY KEY(`session_key`)
);
ALTER TABLE
    `django_session` ADD INDEX `django_session_expire_date_index`(`expire_date`);
CREATE TABLE `emaildigest_anonymoussubscription`(
    `subscription_ptr_id` CHAR(255) NOT NULL,
    `email` VARCHAR(255) NULL,
    `verified` TINYINT NOT NULL,
    `verified_at` DATETIME NULL,
    `verification_code` CHAR(255) NOT NULL,
    `logged_in_user_id` CHAR(255) NULL,
    PRIMARY KEY(`subscription_ptr_id`)
);
ALTER TABLE
    `emaildigest_anonymoussubscription` ADD INDEX `emaildigest_anonymoussubscription_logged_in_user_id_index`(`logged_in_user_id`);
CREATE TABLE `emaildigest_emaildigest`(
    `id` CHAR(255) NOT NULL,
    `created_at` DATETIME NOT NULL,
    `changed_at` DATETIME NOT NULL,
    `frequency` VARCHAR(255) NOT NULL,
    `weekly_weekday` VARCHAR(255) NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `emaildigest_emaildigest_stories`(
    `id` INT NOT NULL,
    `emaildigest_id` CHAR(255) NOT NULL,
    `story_id` CHAR(255) NOT NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `emaildigest_emaildigest_stories` ADD UNIQUE `emaildigest_emaildigest_stories_emaildigest_id_story_id_unique`(`emaildigest_id`, `story_id`);
ALTER TABLE
    `emaildigest_emaildigest_stories` ADD INDEX `emaildigest_emaildigest_stories_story_id_index`(`story_id`);
CREATE TABLE `emaildigest_subscription`(
    `id` CHAR(255) NOT NULL,
    `created_at` DATETIME NOT NULL,
    `changed_at` DATETIME NOT NULL,
    `frequency` VARCHAR(255) NOT NULL,
    `weekly_weekday` VARCHAR(255) NULL,
    `verfied_email` VARCHAR(255) NULL,
    `is_active` TINYINT NOT NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `emaildigest_unsubscription`(
    `id` CHAR(255) NOT NULL,
    `created_at` DATETIME NOT NULL,
    `changed_at` DATETIME NOT NULL,
    `from_digest_id` CHAR(255) NULL,
    `subscription_id` CHAR(255) NOT NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `emaildigest_unsubscription` ADD INDEX `emaildigest_unsubscription_from_digest_id_index`(`from_digest_id`);
ALTER TABLE
    `emaildigest_unsubscription` ADD INDEX `emaildigest_unsubscription_subscription_id_index`(`subscription_id`);
CREATE TABLE `emaildigest_usersubscription`(
    `subscription_ptr_id` CHAR(255) NOT NULL,
    `user_id` CHAR(255) NULL,
    PRIMARY KEY(`subscription_ptr_id`)
);
ALTER TABLE
    `emaildigest_usersubscription` ADD INDEX `emaildigest_usersubscription_user_id_index`(`user_id`);
CREATE TABLE `news_comment`(
    `item_ptr_id` CHAR(255) NOT NULL,
    `text` LONGTEXT NOT NULL,
    `to_story_id` CHAR(255) NOT NULL,
    PRIMARY KEY(`item_ptr_id`)
);
ALTER TABLE
    `news_comment` ADD INDEX `news_comment_to_story_id_index`(`to_story_id`);
CREATE TABLE `news_item`(
    `id` CHAR(255) NOT NULL,
    `created_at` DATETIME NOT NULL,
    `changed_at` DATETIME NOT NULL,
    `upvotes` INT NOT NULL,
    `downvotes` INT NOT NULL,
    `points` INT NOT NULL,
    `num_comments` INT NOT NULL,
    `lft` INT NOT NULL,
    `rght` INT NOT NULL,
    `tree_id` INT NOT NULL,
    `level` INT NOT NULL,
    `parent_id` CHAR(255) NULL,
    `user_id` CHAR(255) NOT NULL,
    `is_ask` TINYINT NOT NULL,
    `is_show` TINYINT NOT NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `news_item` ADD INDEX `news_item_created_at_points_index`(`created_at`, `points`);
ALTER TABLE
    `news_item` ADD INDEX `news_item_id_created_at_index`(`id`, `created_at`);
ALTER TABLE
    `news_item` ADD INDEX `news_item_id_created_at_index`(`id`, `created_at`);
ALTER TABLE
    `news_item` ADD INDEX `news_item_tree_id_index`(`tree_id`);
ALTER TABLE
    `news_item` ADD INDEX `news_item_parent_id_index`(`parent_id`);
ALTER TABLE
    `news_item` ADD INDEX `news_item_user_id_index`(`user_id`);
CREATE TABLE `news_story`(
    `item_ptr_id` CHAR(255) NOT NULL,
    `url` VARCHAR(255) NULL,
    `text` LONGTEXT NULL,
    `title` VARCHAR(255) NOT NULL,
    `duplicate_of_id` CHAR(255) NULL,
    `domain` VARCHAR(255) NULL,
    PRIMARY KEY(`item_ptr_id`)
);
ALTER TABLE
    `news_story` ADD INDEX `news_story_duplicate_of_id_domain_index`(`duplicate_of_id`, `domain`);
ALTER TABLE
    `news_story` ADD INDEX `news_story_duplicate_of_id_index`(`duplicate_of_id`);
ALTER TABLE
    `news_story` ADD INDEX `news_story_domain_index`(`domain`);
CREATE TABLE `news_vote`(
    `id` CHAR(255) NOT NULL,
    `created_at` DATETIME NOT NULL,
    `changed_at` DATETIME NOT NULL,
    `item_id` CHAR(255) NOT NULL,
    `user_id` CHAR(255) NOT NULL,
    `vote` SMALLINT NOT NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `news_vote` ADD INDEX `news_vote_item_id_index`(`item_id`);
ALTER TABLE
    `news_vote` ADD INDEX `news_vote_user_id_index`(`user_id`);
ALTER TABLE
    `news_item` ADD CONSTRAINT `news_item_parent_id_foreign` FOREIGN KEY(`parent_id`) REFERENCES `news_item`(`id`);
ALTER TABLE
    `news_item` ADD CONSTRAINT `news_item_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `accounts_customuser`(`id`);
ALTER TABLE
    `accounts_customuser_groups` ADD CONSTRAINT `accounts_customuser_groups_customuser_id_foreign` FOREIGN KEY(`customuser_id`) REFERENCES `accounts_customuser`(`id`);
ALTER TABLE
    `accounts_customuser` ADD CONSTRAINT `accounts_customuser_parent_id_foreign` FOREIGN KEY(`parent_id`) REFERENCES `accounts_customuser`(`id`);
ALTER TABLE
    `auth_group_permissions` ADD CONSTRAINT `auth_group_permissions_group_id_foreign` FOREIGN KEY(`group_id`) REFERENCES `auth_group`(`id`);
ALTER TABLE
    `news_story` ADD CONSTRAINT `news_story_duplicate_of_id_foreign` FOREIGN KEY(`duplicate_of_id`) REFERENCES `news_story`(`item_ptr_id`);
ALTER TABLE
    `accounts_customuser_user_permissions` ADD CONSTRAINT `accounts_customuser_user_permissions_permission_id_foreign` FOREIGN KEY(`permission_id`) REFERENCES `auth_permission`(`id`);
ALTER TABLE
    `news_item` ADD CONSTRAINT `news_item_id_foreign` FOREIGN KEY(`id`) REFERENCES `news_story`(`item_ptr_id`);
ALTER TABLE
    `emaildigest_emaildigest_stories` ADD CONSTRAINT `emaildigest_emaildigest_stories_story_id_foreign` FOREIGN KEY(`story_id`) REFERENCES `news_story`(`item_ptr_id`);
ALTER TABLE
    `django_admin_log` ADD CONSTRAINT `django_admin_log_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `accounts_customuser`(`id`);
ALTER TABLE
    `emaildigest_subscription` ADD CONSTRAINT `emaildigest_subscription_id_foreign` FOREIGN KEY(`id`) REFERENCES `emaildigest_anonymoussubscription`(`subscription_ptr_id`);
ALTER TABLE
    `emaildigest_unsubscription` ADD CONSTRAINT `emaildigest_unsubscription_from_digest_id_foreign` FOREIGN KEY(`from_digest_id`) REFERENCES `emaildigest_emaildigest`(`id`);
ALTER TABLE
    `news_item` ADD CONSTRAINT `news_item_id_foreign` FOREIGN KEY(`id`) REFERENCES `news_comment`(`item_ptr_id`);
ALTER TABLE
    `django_admin_log` ADD CONSTRAINT `django_admin_log_content_type_id_foreign` FOREIGN KEY(`content_type_id`) REFERENCES `django_content_type`(`id`);
ALTER TABLE
    `emaildigest_anonymoussubscription` ADD CONSTRAINT `emaildigest_anonymoussubscription_logged_in_user_id_foreign` FOREIGN KEY(`logged_in_user_id`) REFERENCES `accounts_customuser`(`id`);
ALTER TABLE
    `accounts_emailverification` ADD CONSTRAINT `accounts_emailverification_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `accounts_customuser`(`id`);
ALTER TABLE
    `news_vote` ADD CONSTRAINT `news_vote_item_id_foreign` FOREIGN KEY(`item_id`) REFERENCES `news_item`(`id`);
ALTER TABLE
    `accounts_customuser_groups` ADD CONSTRAINT `accounts_customuser_groups_group_id_foreign` FOREIGN KEY(`group_id`) REFERENCES `auth_group`(`id`);
ALTER TABLE
    `accounts_passwordresetrequest` ADD CONSTRAINT `accounts_passwordresetrequest_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `accounts_customuser`(`id`);
ALTER TABLE
    `auth_group_permissions` ADD CONSTRAINT `auth_group_permissions_permission_id_foreign` FOREIGN KEY(`permission_id`) REFERENCES `auth_permission`(`id`);
ALTER TABLE
    `auth_permission` ADD CONSTRAINT `auth_permission_content_type_id_foreign` FOREIGN KEY(`content_type_id`) REFERENCES `django_content_type`(`id`);
ALTER TABLE
    `news_comment` ADD CONSTRAINT `news_comment_to_story_id_foreign` FOREIGN KEY(`to_story_id`) REFERENCES `news_story`(`item_ptr_id`);
ALTER TABLE
    `emaildigest_usersubscription` ADD CONSTRAINT `emaildigest_usersubscription_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `accounts_customuser`(`id`);
ALTER TABLE
    `emaildigest_emaildigest_stories` ADD CONSTRAINT `emaildigest_emaildigest_stories_emaildigest_id_foreign` FOREIGN KEY(`emaildigest_id`) REFERENCES `emaildigest_emaildigest`(`id`);
ALTER TABLE
    `accounts_customuser_user_permissions` ADD CONSTRAINT `accounts_customuser_user_permissions_customuser_id_foreign` FOREIGN KEY(`customuser_id`) REFERENCES `accounts_customuser`(`id`);
ALTER TABLE
    `news_vote` ADD CONSTRAINT `news_vote_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `accounts_customuser`(`id`);
ALTER TABLE
    `emaildigest_unsubscription` ADD CONSTRAINT `emaildigest_unsubscription_subscription_id_foreign` FOREIGN KEY(`subscription_id`) REFERENCES `emaildigest_subscription`(`id`);
ALTER TABLE
    `accounts_invitation` ADD CONSTRAINT `accounts_invitation_inviting_user_id_foreign` FOREIGN KEY(`inviting_user_id`) REFERENCES `accounts_customuser`(`id`);
ALTER TABLE
    `emaildigest_subscription` ADD CONSTRAINT `emaildigest_subscription_id_foreign` FOREIGN KEY(`id`) REFERENCES `emaildigest_usersubscription`(`subscription_ptr_id`);
ALTER TABLE
    `accounts_customuser` ADD CONSTRAINT `accounts_customuser_used_invitation_id_foreign` FOREIGN KEY(`used_invitation_id`) REFERENCES `accounts_invitation`(`id`);