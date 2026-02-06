CREATE TABLE `accounts`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `number` VARCHAR(255) NOT NULL,
    `currency_code` VARCHAR(255) NOT NULL,
    `opening_balance` DOUBLE NOT NULL,
    `bank_name` VARCHAR(255) NULL,
    `bank_phone` VARCHAR(255) NULL,
    `bank_address` TEXT NULL,
    `enabled` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `bill_histories`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `bill_id` INT NOT NULL,
    `status` VARCHAR(255) NOT NULL,
    `notify` TINYINT NOT NULL,
    `description` TEXT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `bill_histories` ADD INDEX `bill_histories_company_id_index`(`company_id`);
CREATE TABLE `bill_item_taxes`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `bill_id` INT NOT NULL,
    `bill_item_id` INT NOT NULL,
    `tax_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `amount` DOUBLE NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `bill_item_taxes` ADD INDEX `bill_item_taxes_company_id_index`(`company_id`);
CREATE TABLE `bill_items`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `bill_id` INT NOT NULL,
    `item_id` INT NULL,
    `name` VARCHAR(255) NOT NULL,
    `sku` VARCHAR(255) NULL,
    `quantity` DOUBLE NOT NULL,
    `price` DOUBLE NOT NULL,
    `total` DOUBLE NOT NULL,
    `tax` DOUBLE NOT NULL,
    `discount_rate` DOUBLE NOT NULL,
    `discount_type` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `bill_items` ADD INDEX `bill_items_company_id_index`(`company_id`);
CREATE TABLE `bill_totals`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `bill_id` INT NOT NULL,
    `code` VARCHAR(255) NULL,
    `name` VARCHAR(255) NOT NULL,
    `amount` DOUBLE NOT NULL,
    `sort_order` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `bill_totals` ADD INDEX `bill_totals_company_id_index`(`company_id`);
CREATE TABLE `bills`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `bill_number` VARCHAR(255) NOT NULL,
    `order_number` VARCHAR(255) NULL,
    `status` VARCHAR(255) NOT NULL,
    `billed_at` DATETIME NOT NULL,
    `due_at` DATETIME NOT NULL,
    `amount` DOUBLE NOT NULL,
    `currency_code` VARCHAR(255) NOT NULL,
    `currency_rate` DOUBLE NOT NULL,
    `category_id` INT NOT NULL,
    `contact_id` INT NOT NULL,
    `contact_name` VARCHAR(255) NOT NULL,
    `contact_email` VARCHAR(255) NULL,
    `contact_tax_number` VARCHAR(255) NULL,
    `contact_phone` VARCHAR(255) NULL,
    `contact_address` TEXT NULL,
    `notes` TEXT NULL,
    `parent_id` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `bills` ADD UNIQUE `bills_company_id_bill_number_deleted_at_unique`(
        `company_id`,
        `bill_number`,
        `deleted_at`
    );
ALTER TABLE
    `bills` ADD INDEX `bills_company_id_index`(`company_id`);
CREATE TABLE `categories`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `type` VARCHAR(255) NOT NULL,
    `color` VARCHAR(255) NOT NULL,
    `enabled` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `categories` ADD INDEX `categories_company_id_index`(`company_id`);
CREATE TABLE `companies`(
    `id` INT NOT NULL,
    `domain` VARCHAR(255) NULL,
    `enabled` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `contacts`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `type` VARCHAR(255) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `email` VARCHAR(255) NULL,
    `user_id` INT NULL,
    `tax_number` VARCHAR(255) NULL,
    `phone` VARCHAR(255) NULL,
    `address` TEXT NULL,
    `website` VARCHAR(255) NULL,
    `currency_code` VARCHAR(255) NOT NULL,
    `enabled` TINYINT NOT NULL,
    `reference` VARCHAR(255) NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `contacts` ADD INDEX `contacts_company_id_type_index`(`company_id`, `type`);
ALTER TABLE
    `contacts` ADD UNIQUE `contacts_company_id_type_email_deleted_at_unique`(
        `company_id`,
        `type`,
        `email`,
        `deleted_at`
    );
ALTER TABLE
    `contacts` ADD INDEX `contacts_company_id_index`(`company_id`);
CREATE TABLE `currencies`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `code` VARCHAR(255) NOT NULL,
    `rate` DOUBLE NOT NULL,
    `precision` VARCHAR(255) NULL,
    `symbol` VARCHAR(255) NULL,
    `symbol_first` INT NOT NULL,
    `decimal_mark` VARCHAR(255) NULL,
    `thousands_separator` VARCHAR(255) NULL,
    `enabled` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `currencies` ADD UNIQUE `currencies_company_id_code_deleted_at_unique`(`company_id`, `code`, `deleted_at`);
ALTER TABLE
    `currencies` ADD INDEX `currencies_company_id_index`(`company_id`);
CREATE TABLE `dashboards`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `enabled` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `dashboards` ADD INDEX `dashboards_company_id_index`(`company_id`);
CREATE TABLE `email_templates`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `alias` VARCHAR(255) NOT NULL,
    `class` VARCHAR(255) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `subject` VARCHAR(255) NOT NULL,
    `body` TEXT NOT NULL,
    `params` TEXT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `email_templates` ADD UNIQUE `email_templates_company_id_alias_deleted_at_unique`(`company_id`, `alias`, `deleted_at`);
ALTER TABLE
    `email_templates` ADD INDEX `email_templates_company_id_index`(`company_id`);
CREATE TABLE `failed_jobs`(
    `id` BIGINT NOT NULL,
    `connection` TEXT NOT NULL,
    `queue` TEXT NOT NULL,
    `payload` LONGTEXT NOT NULL,
    `exception` LONGTEXT NOT NULL,
    `failed_at` TIMESTAMP NOT NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `firewall_ips`(
    `id` INT NOT NULL,
    `ip` VARCHAR(255) NOT NULL,
    `log_id` INT NULL,
    `blocked` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `firewall_ips` ADD UNIQUE `firewall_ips_ip_deleted_at_unique`(`ip`, `deleted_at`);
ALTER TABLE
    `firewall_ips` ADD INDEX `firewall_ips_ip_index`(`ip`);
CREATE TABLE `firewall_logs`(
    `id` INT NOT NULL,
    `ip` VARCHAR(255) NOT NULL,
    `level` VARCHAR(255) NOT NULL,
    `middleware` VARCHAR(255) NOT NULL,
    `user_id` INT NULL,
    `url` VARCHAR(255) NULL,
    `referrer` VARCHAR(255) NULL,
    `request` TEXT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `firewall_logs` ADD INDEX `firewall_logs_ip_index`(`ip`);
CREATE TABLE `invoice_histories`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `invoice_id` INT NOT NULL,
    `status` VARCHAR(255) NOT NULL,
    `notify` TINYINT NOT NULL,
    `description` TEXT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `invoice_histories` ADD INDEX `invoice_histories_company_id_index`(`company_id`);
CREATE TABLE `invoice_item_taxes`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `invoice_id` INT NOT NULL,
    `invoice_item_id` INT NOT NULL,
    `tax_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `amount` DOUBLE NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `invoice_item_taxes` ADD INDEX `invoice_item_taxes_company_id_index`(`company_id`);
CREATE TABLE `invoice_items`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `invoice_id` INT NOT NULL,
    `item_id` INT NULL,
    `name` VARCHAR(255) NOT NULL,
    `sku` VARCHAR(255) NULL,
    `quantity` DOUBLE NOT NULL,
    `price` DOUBLE NOT NULL,
    `total` DOUBLE NOT NULL,
    `tax` DOUBLE NOT NULL,
    `discount_rate` DOUBLE NOT NULL,
    `discount_type` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `invoice_items` ADD INDEX `invoice_items_company_id_index`(`company_id`);
CREATE TABLE `invoice_totals`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `invoice_id` INT NOT NULL,
    `code` VARCHAR(255) NULL,
    `name` VARCHAR(255) NOT NULL,
    `amount` DOUBLE NOT NULL,
    `sort_order` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `invoice_totals` ADD INDEX `invoice_totals_company_id_index`(`company_id`);
CREATE TABLE `invoices`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `invoice_number` VARCHAR(255) NOT NULL,
    `order_number` VARCHAR(255) NULL,
    `status` VARCHAR(255) NOT NULL,
    `invoiced_at` DATETIME NOT NULL,
    `due_at` DATETIME NOT NULL,
    `amount` DOUBLE NOT NULL,
    `currency_code` VARCHAR(255) NOT NULL,
    `currency_rate` DOUBLE NOT NULL,
    `category_id` INT NOT NULL,
    `contact_id` INT NOT NULL,
    `contact_name` VARCHAR(255) NOT NULL,
    `contact_email` VARCHAR(255) NULL,
    `contact_tax_number` VARCHAR(255) NULL,
    `contact_phone` VARCHAR(255) NULL,
    `contact_address` TEXT NULL,
    `notes` TEXT NULL,
    `footer` TEXT NULL,
    `parent_id` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `invoices` ADD UNIQUE `invoices_company_id_invoice_number_deleted_at_unique`(
        `company_id`,
        `invoice_number`,
        `deleted_at`
    );
ALTER TABLE
    `invoices` ADD INDEX `invoices_company_id_index`(`company_id`);
CREATE TABLE `items`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `sku` VARCHAR(255) NULL,
    `description` TEXT NULL,
    `sale_price` DOUBLE NOT NULL,
    `purchase_price` DOUBLE NOT NULL,
    `quantity` INT NOT NULL,
    `category_id` INT NULL,
    `tax_id` INT NULL,
    `enabled` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `items` ADD UNIQUE `items_company_id_sku_deleted_at_unique`(`company_id`, `sku`, `deleted_at`);
ALTER TABLE
    `items` ADD INDEX `items_company_id_index`(`company_id`);
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
CREATE TABLE `media`(
    `id` INT NOT NULL,
    `disk` VARCHAR(255) NOT NULL,
    `directory` VARCHAR(255) NOT NULL,
    `filename` VARCHAR(255) NOT NULL,
    `extension` VARCHAR(255) NOT NULL,
    `mime_type` VARCHAR(255) NOT NULL,
    `aggregate_type` VARCHAR(255) NOT NULL,
    `size` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `media` ADD INDEX `media_disk_directory_index`(`disk`, `directory`);
ALTER TABLE
    `media` ADD UNIQUE `media_disk_directory_filename_extension_deleted_at_unique`(
        `disk`,
        `directory`,
        `filename`,
        `extension`,
        `deleted_at`
    );
ALTER TABLE
    `media` ADD INDEX `media_aggregate_type_index`(`aggregate_type`);
CREATE TABLE `mediables`(
    `media_id` INT NOT NULL,
    `mediable_type` VARCHAR(255) NOT NULL,
    `mediable_id` INT NOT NULL,
    `tag` VARCHAR(255) NOT NULL,
    `order` INT NOT NULL,
    PRIMARY KEY(
        `media_id`,
        `mediable_type`,
        `mediable_id`,
        `tag`
    )
);
ALTER TABLE
    `mediables` ADD INDEX `mediables_tag_index`(`tag`);
ALTER TABLE
    `mediables` ADD INDEX `mediables_order_index`(`order`);
CREATE TABLE `module_histories`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `module_id` INT NOT NULL,
    `category` VARCHAR(255) NOT NULL,
    `version` VARCHAR(255) NOT NULL,
    `description` TEXT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `module_histories` ADD INDEX `module_histories_company_id_module_id_index`(`company_id`, `module_id`);
CREATE TABLE `modules`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `alias` VARCHAR(255) NOT NULL,
    `enabled` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `modules` ADD UNIQUE `modules_company_id_alias_deleted_at_unique`(`company_id`, `alias`, `deleted_at`);
ALTER TABLE
    `modules` ADD INDEX `modules_company_id_index`(`company_id`);
CREATE TABLE `notifications`(
    `id` CHAR(255) NOT NULL,
    `type` VARCHAR(255) NOT NULL,
    `notifiable_type` VARCHAR(255) NOT NULL,
    `notifiable_id` BIGINT NOT NULL,
    `data` TEXT NOT NULL,
    `read_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `password_resets`(
    `email` VARCHAR(255) NOT NULL,
    `token` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP NULL
);
ALTER TABLE
    `password_resets` ADD INDEX `password_resets_email_index`(`email`);
CREATE TABLE `permissions`(
    `id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `display_name` VARCHAR(255) NOT NULL,
    `description` VARCHAR(255) NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `permissions` ADD UNIQUE `permissions_name_unique`(`name`);
CREATE TABLE `reconciliations`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `account_id` INT NOT NULL,
    `started_at` DATETIME NOT NULL,
    `ended_at` DATETIME NOT NULL,
    `closing_balance` DOUBLE NOT NULL,
    `reconciled` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `reconciliations` ADD INDEX `reconciliations_company_id_index`(`company_id`);
CREATE TABLE `recurring`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `recurable_type` VARCHAR(255) NOT NULL,
    `recurable_id` BIGINT NOT NULL,
    `frequency` VARCHAR(255) NOT NULL,
    `interval` INT NOT NULL,
    `started_at` DATETIME NOT NULL,
    `count` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `recurring` ADD INDEX `recurring_company_id_index`(`company_id`);
CREATE TABLE `reports`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `class` VARCHAR(255) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `description` TEXT NOT NULL,
    `settings` TEXT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `reports` ADD INDEX `reports_company_id_index`(`company_id`);
CREATE TABLE `role_permissions`(
    `role_id` INT NOT NULL,
    `permission_id` INT NOT NULL,
    PRIMARY KEY(`role_id`, `permission_id`)
);
CREATE TABLE `roles`(
    `id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `display_name` VARCHAR(255) NOT NULL,
    `description` VARCHAR(255) NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `roles` ADD UNIQUE `roles_name_unique`(`name`);
CREATE TABLE `sessions`(
    `id` VARCHAR(255) NOT NULL,
    `user_id` INT NULL,
    `ip_address` VARCHAR(255) NULL,
    `user_agent` TEXT NULL,
    `payload` TEXT NOT NULL,
    `last_activity` INT NOT NULL
);
CREATE TABLE `settings`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `key` VARCHAR(255) NOT NULL,
    `value` TEXT NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `settings` ADD UNIQUE `settings_company_id_key_unique`(`company_id`, `key`);
ALTER TABLE
    `settings` ADD INDEX `settings_company_id_index`(`company_id`);
CREATE TABLE `taxes`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `rate` DOUBLE NOT NULL,
    `type` VARCHAR(255) NOT NULL,
    `enabled` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `taxes` ADD INDEX `taxes_company_id_index`(`company_id`);
CREATE TABLE `transactions`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `type` VARCHAR(255) NOT NULL,
    `paid_at` DATETIME NOT NULL,
    `amount` DOUBLE NOT NULL,
    `currency_code` VARCHAR(255) NOT NULL,
    `currency_rate` DOUBLE NOT NULL,
    `account_id` INT NOT NULL,
    `document_id` INT NULL,
    `contact_id` INT NULL,
    `category_id` INT NOT NULL,
    `description` TEXT NULL,
    `payment_method` VARCHAR(255) NOT NULL,
    `reference` VARCHAR(255) NULL,
    `parent_id` INT NOT NULL,
    `reconciled` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `transactions` ADD INDEX `transactions_company_id_type_index`(`company_id`, `type`);
CREATE TABLE `transfers`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `expense_transaction_id` INT NOT NULL,
    `income_transaction_id` INT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `transfers` ADD INDEX `transfers_company_id_index`(`company_id`);
CREATE TABLE `user_companies`(
    `user_id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `user_type` VARCHAR(255) NOT NULL,
    PRIMARY KEY(`user_id`, `company_id`, `user_type`)
);
CREATE TABLE `user_dashboards`(
    `user_id` INT NOT NULL,
    `dashboard_id` INT NOT NULL,
    `user_type` VARCHAR(255) NOT NULL,
    PRIMARY KEY(
        `user_id`,
        `dashboard_id`,
        `user_type`
    )
);
CREATE TABLE `user_permissions`(
    `user_id` INT NOT NULL,
    `permission_id` INT NOT NULL,
    `user_type` VARCHAR(255) NOT NULL,
    PRIMARY KEY(
        `user_id`,
        `permission_id`,
        `user_type`
    )
);
CREATE TABLE `user_roles`(
    `user_id` INT NOT NULL,
    `role_id` INT NOT NULL,
    `user_type` VARCHAR(255) NOT NULL,
    PRIMARY KEY(`user_id`, `role_id`, `user_type`)
);
CREATE TABLE `users`(
    `id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `password` VARCHAR(255) NOT NULL,
    `remember_token` VARCHAR(255) NULL,
    `last_logged_in_at` TIMESTAMP NULL,
    `locale` VARCHAR(255) NOT NULL,
    `landing_page` VARCHAR(255) NULL,
    `enabled` TINYINT NOT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `users` ADD UNIQUE `users_email_deleted_at_unique`(`email`, `deleted_at`);
CREATE TABLE `widgets`(
    `id` INT NOT NULL,
    `company_id` INT NOT NULL,
    `dashboard_id` INT NOT NULL,
    `class` VARCHAR(255) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `sort` INT NOT NULL,
    `settings` TEXT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    `deleted_at` TIMESTAMP NULL,
    PRIMARY KEY(`id`)
);
ALTER TABLE
    `widgets` ADD INDEX `widgets_company_id_dashboard_id_index`(`company_id`, `dashboard_id`);
ALTER TABLE
    `bills` ADD CONSTRAINT `bills_category_id_foreign` FOREIGN KEY(`category_id`) REFERENCES `categories`(`id`);
ALTER TABLE
    `user_dashboards` ADD CONSTRAINT `user_dashboards_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `bill_totals` ADD CONSTRAINT `bill_totals_bill_id_foreign` FOREIGN KEY(`bill_id`) REFERENCES `bills`(`id`);
ALTER TABLE
    `widgets` ADD CONSTRAINT `widgets_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `items` ADD CONSTRAINT `items_category_id_foreign` FOREIGN KEY(`category_id`) REFERENCES `categories`(`id`);
ALTER TABLE
    `bills` ADD CONSTRAINT `bills_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `user_companies` ADD CONSTRAINT `user_companies_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `bill_item_taxes` ADD CONSTRAINT `bill_item_taxes_tax_id_foreign` FOREIGN KEY(`tax_id`) REFERENCES `taxes`(`id`);
ALTER TABLE
    `invoice_item_taxes` ADD CONSTRAINT `invoice_item_taxes_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `invoice_totals` ADD CONSTRAINT `invoice_totals_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `user_roles` ADD CONSTRAINT `user_roles_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `contacts` ADD CONSTRAINT `contacts_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `invoices` ADD CONSTRAINT `invoices_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `user_companies` ADD CONSTRAINT `user_companies_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `firewall_logs` ADD CONSTRAINT `firewall_logs_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `bill_item_taxes` ADD CONSTRAINT `bill_item_taxes_bill_item_id_foreign` FOREIGN KEY(`bill_item_id`) REFERENCES `bill_items`(`id`);
ALTER TABLE
    `bill_items` ADD CONSTRAINT `bill_items_bill_id_foreign` FOREIGN KEY(`bill_id`) REFERENCES `bills`(`id`);
ALTER TABLE
    `transactions` ADD CONSTRAINT `transactions_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `bill_totals` ADD CONSTRAINT `bill_totals_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `mediables` ADD CONSTRAINT `mediables_media_id_foreign` FOREIGN KEY(`media_id`) REFERENCES `media`(`id`);
ALTER TABLE
    `bill_item_taxes` ADD CONSTRAINT `bill_item_taxes_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `invoice_items` ADD CONSTRAINT `invoice_items_item_id_foreign` FOREIGN KEY(`item_id`) REFERENCES `items`(`id`);
ALTER TABLE
    `invoice_histories` ADD CONSTRAINT `invoice_histories_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `items` ADD CONSTRAINT `items_tax_id_foreign` FOREIGN KEY(`tax_id`) REFERENCES `taxes`(`id`);
ALTER TABLE
    `items` ADD CONSTRAINT `items_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `reconciliations` ADD CONSTRAINT `reconciliations_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `invoice_histories` ADD CONSTRAINT `invoice_histories_invoice_id_foreign` FOREIGN KEY(`invoice_id`) REFERENCES `invoices`(`id`);
ALTER TABLE
    `module_histories` ADD CONSTRAINT `module_histories_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `transfers` ADD CONSTRAINT `transfers_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `invoice_totals` ADD CONSTRAINT `invoice_totals_invoice_id_foreign` FOREIGN KEY(`invoice_id`) REFERENCES `invoices`(`id`);
ALTER TABLE
    `bill_items` ADD CONSTRAINT `bill_items_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `role_permissions` ADD CONSTRAINT `role_permissions_role_id_foreign` FOREIGN KEY(`role_id`) REFERENCES `roles`(`id`);
ALTER TABLE
    `bill_item_taxes` ADD CONSTRAINT `bill_item_taxes_bill_id_foreign` FOREIGN KEY(`bill_id`) REFERENCES `bills`(`id`);
ALTER TABLE
    `accounts` ADD CONSTRAINT `accounts_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `bill_histories` ADD CONSTRAINT `bill_histories_bill_id_foreign` FOREIGN KEY(`bill_id`) REFERENCES `bills`(`id`);
ALTER TABLE
    `invoice_items` ADD CONSTRAINT `invoice_items_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `invoices` ADD CONSTRAINT `invoices_category_id_foreign` FOREIGN KEY(`category_id`) REFERENCES `categories`(`id`);
ALTER TABLE
    `sessions` ADD CONSTRAINT `sessions_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `widgets` ADD CONSTRAINT `widgets_dashboard_id_foreign` FOREIGN KEY(`dashboard_id`) REFERENCES `dashboards`(`id`);
ALTER TABLE
    `invoice_item_taxes` ADD CONSTRAINT `invoice_item_taxes_invoice_id_foreign` FOREIGN KEY(`invoice_id`) REFERENCES `invoices`(`id`);
ALTER TABLE
    `dashboards` ADD CONSTRAINT `dashboards_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `reports` ADD CONSTRAINT `reports_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `bill_items` ADD CONSTRAINT `bill_items_item_id_foreign` FOREIGN KEY(`item_id`) REFERENCES `items`(`id`);
ALTER TABLE
    `categories` ADD CONSTRAINT `categories_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `user_permissions` ADD CONSTRAINT `user_permissions_permission_id_foreign` FOREIGN KEY(`permission_id`) REFERENCES `permissions`(`id`);
ALTER TABLE
    `invoice_item_taxes` ADD CONSTRAINT `invoice_item_taxes_invoice_item_id_foreign` FOREIGN KEY(`invoice_item_id`) REFERENCES `invoice_items`(`id`);
ALTER TABLE
    `bills` ADD CONSTRAINT `bills_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `user_dashboards` ADD CONSTRAINT `user_dashboards_dashboard_id_foreign` FOREIGN KEY(`dashboard_id`) REFERENCES `dashboards`(`id`);
ALTER TABLE
    `invoices` ADD CONSTRAINT `invoices_contact_id_foreign` FOREIGN KEY(`contact_id`) REFERENCES `contacts`(`id`);
ALTER TABLE
    `recurring` ADD CONSTRAINT `recurring_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `bill_histories` ADD CONSTRAINT `bill_histories_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `role_permissions` ADD CONSTRAINT `role_permissions_permission_id_foreign` FOREIGN KEY(`permission_id`) REFERENCES `permissions`(`id`);
ALTER TABLE
    `user_permissions` ADD CONSTRAINT `user_permissions_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`id`);
ALTER TABLE
    `transactions` ADD CONSTRAINT `transactions_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `user_roles` ADD CONSTRAINT `user_roles_role_id_foreign` FOREIGN KEY(`role_id`) REFERENCES `roles`(`id`);
ALTER TABLE
    `invoice_item_taxes` ADD CONSTRAINT `invoice_item_taxes_tax_id_foreign` FOREIGN KEY(`tax_id`) REFERENCES `taxes`(`id`);
ALTER TABLE
    `transactions` ADD CONSTRAINT `transactions_account_id_foreign` FOREIGN KEY(`account_id`) REFERENCES `accounts`(`id`);
ALTER TABLE
    `module_histories` ADD CONSTRAINT `module_histories_module_id_foreign` FOREIGN KEY(`module_id`) REFERENCES `modules`(`id`);
ALTER TABLE
    `settings` ADD CONSTRAINT `settings_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `modules` ADD CONSTRAINT `modules_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `reconciliations` ADD CONSTRAINT `reconciliations_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `currencies` ADD CONSTRAINT `currencies_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `email_templates` ADD CONSTRAINT `email_templates_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `transactions` ADD CONSTRAINT `transactions_category_id_foreign` FOREIGN KEY(`category_id`) REFERENCES `categories`(`id`);
ALTER TABLE
    `taxes` ADD CONSTRAINT `taxes_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);
ALTER TABLE
    `invoice_items` ADD CONSTRAINT `invoice_items_invoice_id_foreign` FOREIGN KEY(`invoice_id`) REFERENCES `invoices`(`id`);
ALTER TABLE
    `contacts` ADD CONSTRAINT `contacts_company_id_foreign` FOREIGN KEY(`company_id`) REFERENCES `companies`(`id`);