CREATE TABLE `accounts`(
    `id` INT NOT NULL,
    `has_access_to_paid_version_for_free` TINYINT NOT NULL,
    `api_key` VARCHAR(255) NOT NULL,
    `number_of_invitations_sent` INT NULL,
    `default_time_reminder_is_sent` VARCHAR(255) NOT NULL,
    `default_gender_id` INT NULL,
    `stripe_id` VARCHAR(255) NULL,
    `card_brand` VARCHAR(255) NULL,
    `card_last_four` VARCHAR(255) NULL,
    `trial_ends_at` TIMESTAMP NULL,
    `legacy_free_plan_unlimited_contacts` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `accounts` ADD INDEX `accounts_stripe_id_index`(`stripe_id`);
CREATE TABLE `activities`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `activity_type_id` INT NULL,
    `summary` VARCHAR(255) NOT NULL,
    `description` LONGTEXT NULL,
    `happened_at` DATE NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `activity_contact`(
    `activity_id` INT NOT NULL,
    `contact_id` INT NOT NULL,
    `account_id` INT NOT NULL
);
CREATE TABLE `activity_statistics`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `contact_id` INT NOT NULL,
    `year` INT NOT NULL,
    `count` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `activity_type_categories`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `name` VARCHAR(255) NULL,
    `translation_key` VARCHAR(255) NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `activity_types`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `activity_type_category_id` INT NOT NULL,
    `name` VARCHAR(255) NULL,
    `translation_key` VARCHAR(255) NULL,
    `location_type` VARCHAR(255) NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `address_contact_field_label`(
    `contact_field_label_id` BIGINT NOT NULL,
    `address_id` INT NOT NULL,
    `account_id` INT NOT NULL
);
CREATE TABLE `addresses`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `place_id` INT NULL,
    `contact_id` INT NOT NULL,
    `name` VARCHAR(255) NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `api_usage`(
    `id` INT NOT NULL,
    `url` VARCHAR(255) NOT NULL,
    `method` VARCHAR(255) NOT NULL,
    `client_ip` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `audit_logs`(
    `id` BIGINT NOT NULL,
    `account_id` INT NOT NULL,
    `author_id` INT NULL,
    `about_contact_id` INT NULL,
    `author_name` VARCHAR(255) NOT NULL,
    `action` VARCHAR(255) NOT NULL,
    `objects` TEXT NOT NULL,
    `audited_at` DATETIME NOT NULL,
    `should_appear_on_dashboard` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `cache`(
    `key` VARCHAR(255) NOT NULL,
    `value` TEXT NOT NULL,
    `expiration` INT NOT NULL
);
ALTER TABLE
    `cache` ADD UNIQUE `cache_key_unique`(`key`);
CREATE TABLE `calls`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `contact_id` INT NOT NULL,
    `called_at` DATETIME NOT NULL,
    `content` MEDIUMTEXT NULL,
    `contact_called` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `companies`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `website` VARCHAR(255) NULL,
    `number_of_employees` INT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `contact_field_contact_field_label`(
    `contact_field_label_id` BIGINT NOT NULL,
    `contact_field_id` INT NOT NULL,
    `account_id` INT NOT NULL
);
CREATE TABLE `contact_field_labels`(
    `id` BIGINT NOT NULL,
    `account_id` INT NOT NULL,
    `label_i18n` VARCHAR(255) NULL,
    `label` VARCHAR(255) NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `contact_field_types`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `fontawesome_icon` VARCHAR(255) NULL,
    `protocol` VARCHAR(255) NULL,
    `delible` TINYINT NOT NULL,
    `type` VARCHAR(255) NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `contact_fields`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `contact_id` INT NOT NULL,
    `contact_field_type_id` INT NOT NULL,
    `data` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `contact_photo`(
    `contact_id` INT NOT NULL,
    `photo_id` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL
);
CREATE TABLE `contact_tag`(
    `contact_id` INT NOT NULL,
    `tag_id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL
);
CREATE TABLE `contacts`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `first_name` VARCHAR(255) NOT NULL,
    `middle_name` VARCHAR(255) NULL,
    `last_name` VARCHAR(255) NULL,
    `nickname` VARCHAR(255) NULL,
    `gender_id` INT NULL,
    `description` VARCHAR(255) NULL,
    `uuid` CHAR(255) NULL,
    `is_starred` TINYINT NOT NULL,
    `is_partial` TINYINT NOT NULL,
    `is_active` TINYINT NOT NULL,
    `is_dead` TINYINT NOT NULL,
    `deceased_special_date_id` INT NULL,
    `deceased_reminder_id` INT NULL,
    `last_talked_to` DATE NULL,
    `stay_in_touch_frequency` INT NULL,
    `stay_in_touch_trigger_date` DATETIME NULL,
    `birthday_special_date_id` INT NULL,
    `birthday_reminder_id` INT NULL,
    `first_met_through_contact_id` INT NULL,
    `first_met_special_date_id` INT NULL,
    `first_met_reminder_id` INT NULL,
    `first_met_where` VARCHAR(255) NULL,
    `first_met_additional_info` LONGTEXT NULL,
    `job` VARCHAR(255) NULL,
    `company` VARCHAR(255) NULL,
    `food_preferences` LONGTEXT NULL,
    `avatar_source` VARCHAR(255) NOT NULL,
    `avatar_gravatar_url` VARCHAR(255) NULL,
    `avatar_adorable_uuid` CHAR(255) NULL,
    `avatar_adorable_url` VARCHAR(255) NULL,
    `avatar_default_url` VARCHAR(255) NULL,
    `avatar_photo_id` INT NULL,
    `has_avatar` TINYINT NOT NULL,
    `avatar_external_url` VARCHAR(255) NULL,
    `avatar_file_name` VARCHAR(255) NULL,
    `avatar_location` VARCHAR(255) NOT NULL,
    `gravatar_url` VARCHAR(255) NULL,
    `last_consulted_at` TIMESTAMP NULL,
    `number_of_views` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `default_avatar_color` VARCHAR(255) NOT NULL,
    `has_avatar_bool` TINYINT NOT NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `conversations`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `contact_id` INT NOT NULL,
    `contact_field_type_id` INT NOT NULL,
    `happened_at` DATETIME NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `crons`(
    `id` INT NOT NULL,
    `command` VARCHAR(255) NOT NULL,
    `last_run` TIMESTAMP NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `crons` ADD UNIQUE `crons_command_unique`(`command`);
CREATE TABLE `currencies`(
    `id` INT NOT NULL,
    `iso` VARCHAR(255) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `symbol` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `days`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `date` DATE NOT NULL,
    `rate` INT NOT NULL,
    `comment` MEDIUMTEXT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `debts`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `contact_id` INT NOT NULL,
    `in_debt` VARCHAR(255) NOT NULL,
    `status` VARCHAR(255) NOT NULL,
    `amount` DECIMAL(8, 2) NOT NULL,
    `reason` LONGTEXT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `default_activity_type_categories`(
    `id` INT NOT NULL,
    `translation_key` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `default_activity_types`(
    `id` INT NOT NULL,
    `default_activity_type_category_id` INT NOT NULL,
    `translation_key` VARCHAR(255) NOT NULL,
    `location_type` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `default_contact_field_types`(
    `id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `fontawesome_icon` VARCHAR(255) NULL,
    `protocol` VARCHAR(255) NULL,
    `migrated` TINYINT NOT NULL,
    `delible` TINYINT NOT NULL,
    `type` VARCHAR(255) NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `default_contact_modules`(
    `id` INT NOT NULL,
    `key` VARCHAR(255) NOT NULL,
    `translation_key` VARCHAR(255) NOT NULL,
    `delible` TINYINT NOT NULL,
    `active` TINYINT NOT NULL,
    `migrated` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `default_life_event_categories`(
    `id` INT NOT NULL,
    `translation_key` VARCHAR(255) NOT NULL,
    `migrated` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `default_life_event_types`(
    `id` INT NOT NULL,
    `default_life_event_category_id` INT NOT NULL,
    `translation_key` VARCHAR(255) NOT NULL,
    `specific_information_structure` TEXT NULL,
    `migrated` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `default_relationship_type_groups`(
    `id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `delible` TINYINT NOT NULL,
    `migrated` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `default_relationship_types`(
    `id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `name_reverse_relationship` VARCHAR(255) NOT NULL,
    `relationship_type_group_id` INT NOT NULL,
    `delible` TINYINT NOT NULL,
    `migrated` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `documents`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `contact_id` INT NOT NULL,
    `original_filename` VARCHAR(255) NOT NULL,
    `new_filename` VARCHAR(255) NOT NULL,
    `filesize` INT NULL,
    `type` VARCHAR(255) NULL,
    `mime_type` VARCHAR(255) NULL,
    `number_of_downloads` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `emotion_activity`(
    `account_id` INT NOT NULL,
    `activity_id` INT NOT NULL,
    `emotion_id` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL
);
CREATE TABLE `emotion_call`(
    `account_id` INT NOT NULL,
    `call_id` INT NOT NULL,
    `emotion_id` INT NOT NULL,
    `contact_id` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL
);
CREATE TABLE `emotions`(
    `id` INT NOT NULL,
    `emotion_primary_id` INT NOT NULL,
    `emotion_secondary_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `emotions_primary`(
    `id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `emotions_secondary`(
    `id` INT NOT NULL,
    `emotion_primary_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `entries`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `title` VARCHAR(255) NULL,
    `post` LONGTEXT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `failed_jobs`(
    `id` INT NOT NULL,
    `connection` TEXT NOT NULL,
    `queue` TEXT NOT NULL,
    `payload` LONGTEXT NOT NULL,
    `exception` LONGTEXT NOT NULL,
    `failed_at` TIMESTAMP NOT NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `genders`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `type` CHAR(255) NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `gift_photo`(
    `photo_id` INT NOT NULL,
    `gift_id` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`photo_id`, `gift_id`)
);
CREATE TABLE `gifts`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `contact_id` INT NOT NULL,
    `is_for` INT NULL,
    `name` VARCHAR(255) NOT NULL,
    `comment` LONGTEXT NULL,
    `url` LONGTEXT NULL,
    `value` VARCHAR(255) NULL,
    `status` VARCHAR(255) NOT NULL,
    `date` DATETIME NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `import_job_reports`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `import_job_id` INT NOT NULL,
    `contact_information` MEDIUMTEXT NOT NULL,
    `skipped` TINYINT NOT NULL,
    `skip_reason` VARCHAR(255) NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `import_jobs`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `type` VARCHAR(255) NOT NULL,
    `contacts_found` INT NULL,
    `contacts_skipped` INT NULL,
    `contacts_imported` INT NULL,
    `filename` VARCHAR(255) NULL,
    `started_at` DATE NULL,
    `ended_at` DATE NULL,
    `failed` TINYINT NOT NULL,
    `failed_reason` MEDIUMTEXT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `instances`(
    `id` INT NOT NULL,
    `uuid` VARCHAR(255) NOT NULL,
    `current_version` VARCHAR(255) NOT NULL,
    `latest_version` VARCHAR(255) NULL,
    `latest_release_notes` MEDIUMTEXT NULL,
    `number_of_versions_since_current_version` INT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `invitations`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `invited_by_user_id` INT NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `invitation_key` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `jobs`(
    `id` BIGINT NOT NULL,
    `queue` VARCHAR(255) NOT NULL,
    `payload` LONGTEXT NOT NULL,
    `attempts` TINYINT NOT NULL,
    `reserved_at` INT NULL,
    `available_at` INT NOT NULL,
    `created_at` INT NOT NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `jobs` ADD INDEX `jobs_queue_reserved_at_index`(`queue`, `reserved_at`);
CREATE TABLE `journal_entries`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `date` DATETIME NOT NULL,
    `journalable_id` INT NOT NULL,
    `journalable_type` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `life_event_categories`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `default_life_event_category_key` VARCHAR(255) NULL,
    `core_monica_data` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `life_event_types`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `life_event_category_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `default_life_event_type_key` VARCHAR(255) NULL,
    `core_monica_data` TINYINT NOT NULL,
    `specific_information_structure` TEXT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `life_events`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `contact_id` INT NOT NULL,
    `life_event_type_id` INT NOT NULL,
    `reminder_id` INT NULL,
    `name` VARCHAR(255) NULL,
    `note` MEDIUMTEXT NULL,
    `happened_at` DATETIME NOT NULL,
    `happened_at_month_unknown` TINYINT NOT NULL,
    `happened_at_day_unknown` TINYINT NOT NULL,
    `specific_information` TEXT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `messages`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `contact_id` INT NOT NULL,
    `conversation_id` INT NOT NULL,
    `content` LONGTEXT NOT NULL,
    `written_at` DATETIME NOT NULL,
    `written_by_me` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `metadata_love_relationships`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `relationship_id` INT NOT NULL,
    `is_active` TINYINT NOT NULL,
    `notes` MEDIUMTEXT NULL,
    `meet_date` DATETIME NULL,
    `official_date` DATETIME NULL,
    `breakup_date` DATETIME NULL,
    `breakup_reason` MEDIUMTEXT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `modules`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `key` VARCHAR(255) NOT NULL,
    `translation_key` VARCHAR(255) NOT NULL,
    `active` TINYINT NOT NULL,
    `delible` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `notes`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `contact_id` INT NOT NULL,
    `body` MEDIUMTEXT NOT NULL,
    `is_favorited` TINYINT NOT NULL,
    `favorited_at` DATE NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `oauth_access_tokens`(
    `id` VARCHAR(255) NOT NULL,
    `user_id` BIGINT NULL,
    `client_id` BIGINT NOT NULL,
    `name` VARCHAR(255) NULL,
    `scopes` TEXT NULL,
    `revoked` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `expires_at` DATETIME NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `oauth_auth_codes`(
    `id` VARCHAR(255) NOT NULL,
    `user_id` BIGINT NOT NULL,
    `client_id` BIGINT NOT NULL,
    `scopes` TEXT NULL,
    `revoked` TINYINT NOT NULL,
    `expires_at` DATETIME NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `oauth_clients`(
    `id` BIGINT NOT NULL,
    `user_id` BIGINT NULL,
    `name` VARCHAR(255) NOT NULL,
    `secret` VARCHAR(255) NULL,
    `redirect` TEXT NOT NULL,
    `personal_access_client` TINYINT NOT NULL,
    `password_client` TINYINT NOT NULL,
    `revoked` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `oauth_personal_access_clients`(
    `id` BIGINT NOT NULL,
    `client_id` BIGINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `oauth_refresh_tokens`(
    `id` VARCHAR(255) NOT NULL,
    `access_token_id` VARCHAR(255) NOT NULL,
    `revoked` TINYINT NOT NULL,
    `expires_at` DATETIME NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `occupations`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `contact_id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `description` VARCHAR(255) NULL,
    `salary` INT NULL,
    `salary_unit` VARCHAR(255) NULL,
    `currently_works_here` TINYINT NULL,
    `start_date` DATE NULL,
    `end_date` DATE NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `password_resets`(
    `email` VARCHAR(255) NOT NULL,
    `token` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP NOT NULL
);
ALTER TABLE
    `password_resets` ADD INDEX `password_resets_email_index`(`email`);
ALTER TABLE
    `password_resets` ADD INDEX `password_resets_token_index`(`token`);
CREATE TABLE `pet_categories`(
    `id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `is_common` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `pets`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `contact_id` INT NOT NULL,
    `pet_category_id` INT NOT NULL,
    `name` VARCHAR(255) NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `photos`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `original_filename` VARCHAR(255) NOT NULL,
    `new_filename` VARCHAR(255) NOT NULL,
    `filesize` INT NULL,
    `mime_type` VARCHAR(255) NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `places`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `street` VARCHAR(255) NULL,
    `city` VARCHAR(255) NULL,
    `province` VARCHAR(255) NULL,
    `postal_code` VARCHAR(255) NULL,
    `country` CHAR(255) NULL,
    `latitude` DOUBLE NULL,
    `longitude` DOUBLE NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `recovery_codes`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `recovery` VARCHAR(255) NOT NULL,
    `used` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `relationship_type_groups`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `delible` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `relationship_types`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `name_reverse_relationship` VARCHAR(255) NOT NULL,
    `relationship_type_group_id` INT NOT NULL,
    `delible` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `relationships`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `relationship_type_id` INT NOT NULL,
    `contact_is` INT NOT NULL,
    `of_contact` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `reminder_outbox`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `reminder_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `planned_date` DATE NOT NULL,
    `nature` VARCHAR(255) NOT NULL,
    `notification_number_days_before` INT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `reminder_rules`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `number_of_days_before` INT NOT NULL,
    `active` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `reminder_sent`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `reminder_id` INT NULL,
    `user_id` INT NOT NULL,
    `planned_date` DATE NOT NULL,
    `sent_date` DATETIME NOT NULL,
    `nature` VARCHAR(255) NOT NULL,
    `frequency_type` VARCHAR(255) NULL,
    `frequency_number` INT NULL,
    `html_content` LONGTEXT NULL,
    `text_content` LONGTEXT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `reminders`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `contact_id` INT NOT NULL,
    `initial_date` DATE NOT NULL,
    `title` MEDIUMTEXT NULL,
    `description` LONGTEXT NULL,
    `frequency_type` VARCHAR(255) NOT NULL,
    `frequency_number` INT NULL,
    `delible` TINYINT NOT NULL,
    `inactive` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `sessions`(
    `id` VARCHAR(255) NOT NULL,
    `user_id` INT NULL,
    `ip_address` VARCHAR(255) NULL,
    `user_agent` TEXT NULL,
    `payload` TEXT NOT NULL,
    `last_activity` INT NOT NULL
);
ALTER TABLE
    `sessions` ADD UNIQUE `sessions_id_unique`(`id`);
CREATE TABLE `special_dates`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `contact_id` INT NOT NULL,
    `uuid` CHAR(255) NULL,
    `is_age_based` TINYINT NOT NULL,
    `is_year_unknown` TINYINT NOT NULL,
    `date` DATE NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `special_dates` ADD INDEX `special_dates_account_id_uuid_index`(`account_id`, `uuid`);
CREATE TABLE `statistics`(
    `id` INT NOT NULL,
    `number_of_users` INT NOT NULL,
    `number_of_contacts` INT NOT NULL,
    `number_of_notes` INT NOT NULL,
    `number_of_oauth_access_tokens` INT NOT NULL,
    `number_of_oauth_clients` INT NOT NULL,
    `number_of_offsprings` INT NOT NULL,
    `number_of_progenitors` INT NOT NULL,
    `number_of_relationships` INT NOT NULL,
    `number_of_subscriptions` INT NOT NULL,
    `number_of_reminders` INT NOT NULL,
    `number_of_tasks` INT NOT NULL,
    `number_of_kids` INT NOT NULL,
    `number_of_activities` INT NOT NULL,
    `number_of_addresses` INT NOT NULL,
    `number_of_api_calls` INT NOT NULL,
    `number_of_calls` INT NOT NULL,
    `number_of_contact_fields` INT NOT NULL,
    `number_of_contact_field_types` INT NOT NULL,
    `number_of_debts` INT NOT NULL,
    `number_of_entries` INT NOT NULL,
    `number_of_gifts` INT NOT NULL,
    `number_of_invitations_sent` INT NULL,
    `number_of_accounts_with_more_than_one_user` INT NULL,
    `number_of_tags` INT NULL,
    `number_of_import_jobs` INT NULL,
    `number_of_conversations` INT NULL,
    `number_of_messages` INT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `subscriptions`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `stripe_id` VARCHAR(255) NOT NULL,
    `stripe_status` VARCHAR(255) NOT NULL,
    `stripe_plan` VARCHAR(255) NOT NULL,
    `quantity` INT NOT NULL,
    `trial_ends_at` TIMESTAMP NULL,
    `ends_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `subscriptions` ADD INDEX `subscriptions_account_id_stripe_status_index`(`account_id`, `stripe_status`);
CREATE TABLE `synctoken`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `timestamp` TIMESTAMP NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `synctoken` ADD INDEX `synctoken_account_id_user_id_name_index`(`account_id`, `user_id`, `name`);
CREATE TABLE `tags`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `name_slug` VARCHAR(255) NOT NULL,
    `description` MEDIUMTEXT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `tasks`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `contact_id` INT NULL,
    `uuid` CHAR(255) NULL,
    `title` VARCHAR(255) NOT NULL,
    `description` LONGTEXT NULL,
    `completed` TINYINT NOT NULL,
    `completed_at` DATETIME NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `tasks` ADD INDEX `tasks_account_id_uuid_index`(`account_id`, `uuid`);
CREATE TABLE `term_user`(
    `account_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `term_id` INT NOT NULL,
    `ip_address` VARCHAR(255) NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL
);
CREATE TABLE `terms`(
    `id` INT NOT NULL,
    `term_version` VARCHAR(255) NOT NULL,
    `term_content` MEDIUMTEXT NOT NULL,
    `privacy_version` VARCHAR(255) NOT NULL,
    `privacy_content` MEDIUMTEXT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `u2f_key`(
    `id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `user_id` INT NOT NULL,
    `keyHandle` VARCHAR(255) NOT NULL,
    `publicKey` VARCHAR(255) NOT NULL,
    `certificate` TEXT NOT NULL,
    `counter` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `u2f_key` ADD UNIQUE `u2f_key_publickey_unique`(`publicKey`);
CREATE TABLE `users`(
    `id` INT NOT NULL,
    `first_name` VARCHAR(255) NOT NULL,
    `last_name` VARCHAR(255) NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `me_contact_id` INT NULL,
    `admin` TINYINT NOT NULL,
    `email_verified_at` TIMESTAMP NULL,
    `password` VARCHAR(255) NOT NULL,
    `remember_token` VARCHAR(255) NULL,
    `google2fa_secret` VARCHAR(255) NULL,
    `account_id` INT NOT NULL,
    `timezone` VARCHAR(255) NULL,
    `currency_id` INT NULL,
    `locale` VARCHAR(255) NOT NULL,
    `metric` VARCHAR(255) NOT NULL,
    `fluid_container` VARCHAR(255) NOT NULL,
    `contacts_sort_order` VARCHAR(255) NOT NULL,
    `name_order` VARCHAR(255) NOT NULL,
    `invited_by_user_id` INT NULL,
    `dashboard_active_tab` VARCHAR(255) NOT NULL,
    `gifts_active_tab` VARCHAR(255) NOT NULL,
    `profile_active_tab` VARCHAR(255) NOT NULL,
    `profile_new_life_event_badge_seen` TINYINT NOT NULL,
    `temperature_scale` VARCHAR(255) NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `users` ADD UNIQUE `users_email_unique`(`email`);
CREATE TABLE `weather`(
    `id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `place_id` INT NOT NULL,
    `weather_json` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `webauthn_keys`(
    `id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `credentialId` VARCHAR(255) NOT NULL,
    `type` VARCHAR(255) NOT NULL,
    `transports` TEXT NOT NULL,
    `attestationType` VARCHAR(255) NOT NULL,
    `trustPath` TEXT NOT NULL,
    `aaguid` TEXT NOT NULL,
    `credentialPublicKey` TEXT NOT NULL,
    `counter` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `webauthn_keys` ADD INDEX `webauthn_keys_credentialid_index`(`credentialId`);
ALTER TABLE
    `debts` ADD CONSTRAINT `debts_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `days` ADD CONSTRAINT `days_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `emotion_call` ADD CONSTRAINT `emotion_call_emotion_id_foreign` FOREIGN KEY(`emotion_id`) REFERENCES `emotions`(`id`);
ALTER TABLE
    `life_events` ADD CONSTRAINT `life_events_life_event_type_id_foreign` FOREIGN KEY(`life_event_type_id`) REFERENCES `life_event_types`(`id`);
ALTER TABLE
    `messages` ADD CONSTRAINT `messages_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `pets` ADD CONSTRAINT `pets_pet_category_id_foreign` FOREIGN KEY(`pet_category_id`) REFERENCES `pet_categories`(`id`);
ALTER TABLE
    `contact_field_labels` ADD CONSTRAINT `contact_field_labels_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `relationships` ADD CONSTRAINT `relationships_of_contact_foreign` FOREIGN KEY(`of_contact`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `import_jobs` ADD CONSTRAINT `import_jobs_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `reminder_sent` ADD CONSTRAINT `reminder_sent_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `activity_contact` ADD CONSTRAINT `activity_contact_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `tags` ADD CONSTRAINT `tags_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `activity_statistics` ADD CONSTRAINT `activity_statistics_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `contact_field_labels` ADD CONSTRAINT `contact_field_labels_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `oauth_clients` ADD CONSTRAINT `oauth_clients_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `audit_logs` ADD CONSTRAINT `audit_logs_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `contact_tag` ADD CONSTRAINT `contact_tag_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `import_job_reports` ADD CONSTRAINT `import_job_reports_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `modules` ADD CONSTRAINT `modules_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `term_user` ADD CONSTRAINT `term_user_term_id_foreign` FOREIGN KEY(`term_id`) REFERENCES `terms`(`id`);
ALTER TABLE
    `reminder_sent` ADD CONSTRAINT `reminder_sent_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `documents` ADD CONSTRAINT `documents_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `companies` ADD CONSTRAINT `companies_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `synctoken` ADD CONSTRAINT `synctoken_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `relationships` ADD CONSTRAINT `relationships_relationship_type_id_foreign` FOREIGN KEY(`relationship_type_id`) REFERENCES `relationship_types`(`id`);
ALTER TABLE
    `reminder_outbox` ADD CONSTRAINT `reminder_outbox_reminder_id_foreign` FOREIGN KEY(`reminder_id`) REFERENCES `reminders`(`id`);
ALTER TABLE
    `gift_photo` ADD CONSTRAINT `gift_photo_photo_id_foreign` FOREIGN KEY(`photo_id`) REFERENCES `photos`(`id`);
ALTER TABLE
    `u2f_key` ADD CONSTRAINT `u2f_key_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `life_events` ADD CONSTRAINT `life_events_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `life_event_categories` ADD CONSTRAINT `life_event_categories_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `entries` ADD CONSTRAINT `entries_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `occupations` ADD CONSTRAINT `occupations_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `weather` ADD CONSTRAINT `weather_place_id_foreign` FOREIGN KEY(`place_id`) REFERENCES `places`(`id`);
ALTER TABLE
    `notes` ADD CONSTRAINT `notes_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `pets` ADD CONSTRAINT `pets_pet_category_id_foreign` FOREIGN KEY(`pet_category_id`) REFERENCES `pet_categories`(`id`);
ALTER TABLE
    `relationships` ADD CONSTRAINT `relationships_relationship_type_id_foreign` FOREIGN KEY(`relationship_type_id`) REFERENCES `relationship_types`(`id`);
ALTER TABLE
    `reminder_rules` ADD CONSTRAINT `reminder_rules_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `pets` ADD CONSTRAINT `pets_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `invitations` ADD CONSTRAINT `invitations_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `relationship_type_groups` ADD CONSTRAINT `relationship_type_groups_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `emotion_call` ADD CONSTRAINT `emotion_call_call_id_foreign` FOREIGN KEY(`call_id`) REFERENCES `calls`(`id`);
ALTER TABLE
    `users` ADD CONSTRAINT `users_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `documents` ADD CONSTRAINT `documents_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `occupations` ADD CONSTRAINT `occupations_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `emotion_activity` ADD CONSTRAINT `emotion_activity_activity_id_foreign` FOREIGN KEY(`activity_id`) REFERENCES `activities`(`id`);
ALTER TABLE
    `addresses` ADD CONSTRAINT `addresses_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `term_user` ADD CONSTRAINT `term_user_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `relationship_types` ADD CONSTRAINT `relationship_types_relationship_type_group_id_foreign` FOREIGN KEY(`relationship_type_group_id`) REFERENCES `relationship_type_groups`(`id`);
ALTER TABLE
    `debts` ADD CONSTRAINT `debts_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `calls` ADD CONSTRAINT `calls_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `contact_tag` ADD CONSTRAINT `contact_tag_tag_id_foreign` FOREIGN KEY(`tag_id`) REFERENCES `tags`(`id`);
ALTER TABLE
    `contacts` ADD CONSTRAINT `contacts_gender_id_foreign` FOREIGN KEY(`gender_id`) REFERENCES `genders`(`id`);
ALTER TABLE
    `relationship_types` ADD CONSTRAINT `relationship_types_relationship_type_group_id_foreign` FOREIGN KEY(`relationship_type_group_id`) REFERENCES `relationship_type_groups`(`id`);
ALTER TABLE
    `contacts` ADD CONSTRAINT `contacts_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `synctoken` ADD CONSTRAINT `synctoken_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `sessions` ADD CONSTRAINT `sessions_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `term_user` ADD CONSTRAINT `term_user_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `days` ADD CONSTRAINT `days_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `activity_types` ADD CONSTRAINT `activity_types_activity_type_category_id_foreign` FOREIGN KEY(`activity_type_category_id`) REFERENCES `activity_type_categories`(`id`);
ALTER TABLE
    `gifts` ADD CONSTRAINT `gifts_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `life_events` ADD CONSTRAINT `life_events_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `genders` ADD CONSTRAINT `genders_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `gift_photo` ADD CONSTRAINT `gift_photo_gift_id_foreign` FOREIGN KEY(`gift_id`) REFERENCES `gifts`(`id`);
ALTER TABLE
    `contact_tag` ADD CONSTRAINT `contact_tag_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `users` ADD CONSTRAINT `users_me_contact_id_foreign` FOREIGN KEY(`me_contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `life_events` ADD CONSTRAINT `life_events_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `default_relationship_types` ADD CONSTRAINT `default_relationship_types_relationship_type_group_id_foreign` FOREIGN KEY(`relationship_type_group_id`) REFERENCES `relationship_type_groups`(`id`);
ALTER TABLE
    `occupations` ADD CONSTRAINT `occupations_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `reminders` ADD CONSTRAINT `reminders_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `gifts` ADD CONSTRAINT `gifts_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `occupations` ADD CONSTRAINT `occupations_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `activity_types` ADD CONSTRAINT `activity_types_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `metadata_love_relationships` ADD CONSTRAINT `metadata_love_relationships_relationship_id_foreign` FOREIGN KEY(`relationship_id`) REFERENCES `relationships`(`id`);
ALTER TABLE
    `contact_photo` ADD CONSTRAINT `contact_photo_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `activity_types` ADD CONSTRAINT `activity_types_activity_type_category_id_foreign` FOREIGN KEY(`activity_type_category_id`) REFERENCES `activity_type_categories`(`id`);
ALTER TABLE
    `emotion_activity` ADD CONSTRAINT `emotion_activity_activity_id_foreign` FOREIGN KEY(`activity_id`) REFERENCES `activities`(`id`);
ALTER TABLE
    `debts` ADD CONSTRAINT `debts_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `users` ADD CONSTRAINT `users_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `activity_contact` ADD CONSTRAINT `activity_contact_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `notes` ADD CONSTRAINT `notes_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `special_dates` ADD CONSTRAINT `special_dates_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `relationship_type_groups` ADD CONSTRAINT `relationship_type_groups_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `documents` ADD CONSTRAINT `documents_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `emotion_activity` ADD CONSTRAINT `emotion_activity_emotion_id_foreign` FOREIGN KEY(`emotion_id`) REFERENCES `emotions`(`id`);
ALTER TABLE
    `relationships` ADD CONSTRAINT `relationships_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `activity_type_categories` ADD CONSTRAINT `activity_type_categories_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `recovery_codes` ADD CONSTRAINT `recovery_codes_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `emotion_call` ADD CONSTRAINT `emotion_call_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `life_event_types` ADD CONSTRAINT `life_event_types_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `import_jobs` ADD CONSTRAINT `import_jobs_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `emotion_call` ADD CONSTRAINT `emotion_call_call_id_foreign` FOREIGN KEY(`call_id`) REFERENCES `calls`(`id`);
ALTER TABLE
    `contact_field_contact_field_label` ADD CONSTRAINT `contact_field_contact_field_label_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `activities` ADD CONSTRAINT `activities_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `default_activity_types` ADD CONSTRAINT `default_activity_types_default_activity_type_category_id_foreign` FOREIGN KEY(
        `default_activity_type_category_id`
    ) REFERENCES `default_activity_type_categories`(`id`);
ALTER TABLE
    `address_contact_field_label` ADD CONSTRAINT `address_contact_field_label_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `oauth_auth_codes` ADD CONSTRAINT `oauth_auth_codes_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `recovery_codes` ADD CONSTRAINT `recovery_codes_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `contact_field_types` ADD CONSTRAINT `contact_field_types_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `webauthn_keys` ADD CONSTRAINT `webauthn_keys_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `reminder_outbox` ADD CONSTRAINT `reminder_outbox_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `journal_entries` ADD CONSTRAINT `journal_entries_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `messages` ADD CONSTRAINT `messages_conversation_id_foreign` FOREIGN KEY(`conversation_id`) REFERENCES `conversations`(`id`);
ALTER TABLE
    `places` ADD CONSTRAINT `places_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `contact_field_contact_field_label` ADD CONSTRAINT `contact_field_contact_field_label_contact_field_label_id_foreign` FOREIGN KEY(`contact_field_label_id`) REFERENCES `contact_field_labels`(`id`);
ALTER TABLE
    `genders` ADD CONSTRAINT `genders_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `weather` ADD CONSTRAINT `weather_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `pets` ADD CONSTRAINT `pets_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `life_event_categories` ADD CONSTRAINT `life_event_categories_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `reminders` ADD CONSTRAINT `reminders_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `subscriptions` ADD CONSTRAINT `subscriptions_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `contact_field_contact_field_label` ADD CONSTRAINT `contact_field_contact_field_label_contact_field_id_foreign` FOREIGN KEY(`contact_field_id`) REFERENCES `contact_fields`(`id`);
ALTER TABLE
    `default_life_event_types` ADD CONSTRAINT `default_life_event_types_default_life_event_category_id_foreign` FOREIGN KEY(`default_life_event_category_id`) REFERENCES `default_life_event_categories`(`id`);
ALTER TABLE
    `messages` ADD CONSTRAINT `messages_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `weather` ADD CONSTRAINT `weather_place_id_foreign` FOREIGN KEY(`place_id`) REFERENCES `places`(`id`);
ALTER TABLE
    `tasks` ADD CONSTRAINT `tasks_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `contact_photo` ADD CONSTRAINT `contact_photo_photo_id_foreign` FOREIGN KEY(`photo_id`) REFERENCES `photos`(`id`);
ALTER TABLE
    `occupations` ADD CONSTRAINT `occupations_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `relationships` ADD CONSTRAINT `relationships_contact_is_foreign` FOREIGN KEY(`contact_is`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `import_job_reports` ADD CONSTRAINT `import_job_reports_import_job_id_foreign` FOREIGN KEY(`import_job_id`) REFERENCES `import_jobs`(`id`);
ALTER TABLE
    `contacts` ADD CONSTRAINT `contacts_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `audit_logs` ADD CONSTRAINT `audit_logs_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `synctoken` ADD CONSTRAINT `synctoken_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `activity_type_categories` ADD CONSTRAINT `activity_type_categories_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `conversations` ADD CONSTRAINT `conversations_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `contact_field_contact_field_label` ADD CONSTRAINT `contact_field_contact_field_label_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `activity_statistics` ADD CONSTRAINT `activity_statistics_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `activity_contact` ADD CONSTRAINT `activity_contact_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `activities` ADD CONSTRAINT `activities_activity_type_id_foreign` FOREIGN KEY(`activity_type_id`) REFERENCES `activity_types`(`id`);
ALTER TABLE
    `addresses` ADD CONSTRAINT `addresses_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `photos` ADD CONSTRAINT `photos_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `emotion_call` ADD CONSTRAINT `emotion_call_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `address_contact_field_label` ADD CONSTRAINT `address_contact_field_label_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `activity_statistics` ADD CONSTRAINT `activity_statistics_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `contact_tag` ADD CONSTRAINT `contact_tag_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `special_dates` ADD CONSTRAINT `special_dates_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `companies` ADD CONSTRAINT `companies_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `import_job_reports` ADD CONSTRAINT `import_job_reports_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `reminder_sent` ADD CONSTRAINT `reminder_sent_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `life_event_types` ADD CONSTRAINT `life_event_types_life_event_category_id_foreign` FOREIGN KEY(`life_event_category_id`) REFERENCES `life_event_categories`(`id`);
ALTER TABLE
    `activity_types` ADD CONSTRAINT `activity_types_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `special_dates` ADD CONSTRAINT `special_dates_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `documents` ADD CONSTRAINT `documents_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `tasks` ADD CONSTRAINT `tasks_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `conversations` ADD CONSTRAINT `conversations_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `calls` ADD CONSTRAINT `calls_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `addresses` ADD CONSTRAINT `addresses_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `gifts` ADD CONSTRAINT `gifts_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `journal_entries` ADD CONSTRAINT `journal_entries_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `notes` ADD CONSTRAINT `notes_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `metadata_love_relationships` ADD CONSTRAINT `metadata_love_relationships_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `reminder_outbox` ADD CONSTRAINT `reminder_outbox_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `users` ADD CONSTRAINT `users_invited_by_user_id_foreign` FOREIGN KEY(`invited_by_user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `calls` ADD CONSTRAINT `calls_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `users` ADD CONSTRAINT `users_currency_id_foreign` FOREIGN KEY(`currency_id`) REFERENCES `currencies`(`id`);
ALTER TABLE
    `term_user` ADD CONSTRAINT `term_user_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `contact_fields` ADD CONSTRAINT `contact_fields_contact_field_type_id_foreign` FOREIGN KEY(`contact_field_type_id`) REFERENCES `contact_field_types`(`id`);
ALTER TABLE
    `reminders` ADD CONSTRAINT `reminders_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `pets` ADD CONSTRAINT `pets_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `import_jobs` ADD CONSTRAINT `import_jobs_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `contact_fields` ADD CONSTRAINT `contact_fields_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `addresses` ADD CONSTRAINT `addresses_place_id_foreign` FOREIGN KEY(`place_id`) REFERENCES `places`(`id`);
ALTER TABLE
    `emotion_activity` ADD CONSTRAINT `emotion_activity_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `conversations` ADD CONSTRAINT `conversations_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `address_contact_field_label` ADD CONSTRAINT `address_contact_field_label_contact_field_label_id_foreign` FOREIGN KEY(`contact_field_label_id`) REFERENCES `contact_field_labels`(`id`);
ALTER TABLE
    `life_event_types` ADD CONSTRAINT `life_event_types_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `address_contact_field_label` ADD CONSTRAINT `address_contact_field_label_address_id_foreign` FOREIGN KEY(`address_id`) REFERENCES `addresses`(`id`);
ALTER TABLE
    `life_event_types` ADD CONSTRAINT `life_event_types_life_event_category_id_foreign` FOREIGN KEY(`life_event_category_id`) REFERENCES `life_event_categories`(`id`);
ALTER TABLE
    `reminder_rules` ADD CONSTRAINT `reminder_rules_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `reminder_outbox` ADD CONSTRAINT `reminder_outbox_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `conversations` ADD CONSTRAINT `conversations_contact_field_type_id_foreign` FOREIGN KEY(`contact_field_type_id`) REFERENCES `contact_field_types`(`id`);
ALTER TABLE
    `emotion_call` ADD CONSTRAINT `emotion_call_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `reminders` ADD CONSTRAINT `reminders_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `conversations` ADD CONSTRAINT `conversations_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `messages` ADD CONSTRAINT `messages_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `photos` ADD CONSTRAINT `photos_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `tasks` ADD CONSTRAINT `tasks_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `contact_field_types` ADD CONSTRAINT `contact_field_types_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `special_dates` ADD CONSTRAINT `special_dates_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `gifts` ADD CONSTRAINT `gifts_is_for_foreign` FOREIGN KEY(`is_for`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `gifts` ADD CONSTRAINT `gifts_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `occupations` ADD CONSTRAINT `occupations_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `life_events` ADD CONSTRAINT `life_events_life_event_type_id_foreign` FOREIGN KEY(`life_event_type_id`) REFERENCES `life_event_types`(`id`);
ALTER TABLE
    `users` ADD CONSTRAINT `users_currency_id_foreign` FOREIGN KEY(`currency_id`) REFERENCES `currencies`(`id`);
ALTER TABLE
    `contact_fields` ADD CONSTRAINT `contact_fields_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `recovery_codes` ADD CONSTRAINT `recovery_codes_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `pets` ADD CONSTRAINT `pets_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `contact_fields` ADD CONSTRAINT `contact_fields_contact_field_type_id_foreign` FOREIGN KEY(`contact_field_type_id`) REFERENCES `contact_field_types`(`id`);
ALTER TABLE
    `oauth_access_tokens` ADD CONSTRAINT `oauth_access_tokens_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `weather` ADD CONSTRAINT `weather_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `messages` ADD CONSTRAINT `messages_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `tasks` ADD CONSTRAINT `tasks_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `life_events` ADD CONSTRAINT `life_events_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `metadata_love_relationships` ADD CONSTRAINT `metadata_love_relationships_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `relationship_types` ADD CONSTRAINT `relationship_types_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `life_events` ADD CONSTRAINT `life_events_reminder_id_foreign` FOREIGN KEY(`reminder_id`) REFERENCES `reminders`(`id`);
ALTER TABLE
    `emotion_activity` ADD CONSTRAINT `emotion_activity_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `import_job_reports` ADD CONSTRAINT `import_job_reports_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `webauthn_keys` ADD CONSTRAINT `webauthn_keys_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `default_life_event_types` ADD CONSTRAINT `default_life_event_types_default_life_event_category_id_foreign` FOREIGN KEY(`default_life_event_category_id`) REFERENCES `default_life_event_categories`(`id`);
ALTER TABLE
    `relationship_types` ADD CONSTRAINT `relationship_types_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `activity_contact` ADD CONSTRAINT `activity_contact_activity_id_foreign` FOREIGN KEY(`activity_id`) REFERENCES `activities`(`id`);
ALTER TABLE
    `messages` ADD CONSTRAINT `messages_conversation_id_foreign` FOREIGN KEY(`conversation_id`) REFERENCES `conversations`(`id`);
ALTER TABLE
    `relationships` ADD CONSTRAINT `relationships_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `contact_fields` ADD CONSTRAINT `contact_fields_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `modules` ADD CONSTRAINT `modules_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `debts` ADD CONSTRAINT `debts_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `activities` ADD CONSTRAINT `activities_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `entries` ADD CONSTRAINT `entries_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `tags` ADD CONSTRAINT `tags_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `invitations` ADD CONSTRAINT `invitations_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `emotion_call` ADD CONSTRAINT `emotion_call_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `activity_contact` ADD CONSTRAINT `activity_contact_activity_id_foreign` FOREIGN KEY(`activity_id`) REFERENCES `activities`(`id`);
ALTER TABLE
    `conversations` ADD CONSTRAINT `conversations_contact_field_type_id_foreign` FOREIGN KEY(`contact_field_type_id`) REFERENCES `contact_field_types`(`id`);
ALTER TABLE
    `notes` ADD CONSTRAINT `notes_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `places` ADD CONSTRAINT `places_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `reminder_sent` ADD CONSTRAINT `reminder_sent_reminder_id_foreign` FOREIGN KEY(`reminder_id`) REFERENCES `reminders`(`id`);
ALTER TABLE
    `emotions_secondary` ADD CONSTRAINT `emotions_secondary_emotion_primary_id_foreign` FOREIGN KEY(`emotion_primary_id`) REFERENCES `emotions_primary`(`id`);