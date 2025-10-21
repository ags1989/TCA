# Скрипт для перемещения файлов в каталог DELETE

Write-Host "Начинаем перемещение файлов в каталог DELETE..."

# 1. Дублирующиеся конфигурационные файлы
Write-Host "Перемещаем дублирующиеся конфигурационные файлы..."
if (Test-Path "env.tfs.example") { Move-Item "env.tfs.example" "DELETE\config_duplicates\" }
if (Test-Path "setup_env.py") { Move-Item "setup_env.py" "DELETE\utilities\" }

# 2. Отладочные скрипты
Write-Host "Перемещаем отладочные скрипты..."
$debugFiles = @(
    "check_all_tickets.py", "check_backlog_item.py", "check_comments.py", 
    "check_created_items.py", "check_env.py", "check_epic_feature_fields.py",
    "check_epic_fields.py", "check_epic_states.py", "check_example_links.py",
    "check_final_result.py", "check_fixed_tickets.py", "check_houston_types.py",
    "check_mars_types.py", "check_new_links.py", "check_required_fields.py",
    "check_upstream_iteration.py", "check_work_item_234585.py", "check_work_item_types.py",
    "check_working_tickets.py", "debug_epic_creation.py", "debug_get_work_item.py",
    "debug_link_creation.py", "debug_tfs_detailed.py", "debug_tfs_openai.py",
    "debug_urls.py", "debug_wiql_bug_search.py", "diagnose_work_item.py",
    "get_backlog_item_234374.py", "get_epic_234370_fields.py", "get_epic_234370.py",
    "get_source_ticket_fields.py"
)

foreach ($file in $debugFiles) {
    if (Test-Path $file) {
        Move-Item $file "DELETE\debug_scripts\"
        Write-Host "Перемещен: $file"
    }
}

# 3. Тестовые скрипты
Write-Host "Перемещаем тестовые скрипты..."
$testFiles = @(
    "test_api_versions.py", "test_async_basic.py", "test_basic.py", "test_batch_api.py",
    "test_change_chain.py", "test_checklist_fixes.py", "test_config.py", "test_confluence_auth.py",
    "test_confluence_connection.py", "test_confluence_full.py", "test_confluence_parsing.py",
    "test_enhanced_215042.py", "test_env_loading.py", "test_houston_backlog.py", "test_imports.py",
    "test_link_types.py", "test_logic_fixes.py", "test_optimized_checklist.py", "test_optimized_user_story.py",
    "test_performance_optimization.py", "test_real_tfs_data.py", "test_services_debug.py",
    "test_services.py", "test_test_case_logic.py", "test_tfs_service.py", "test_updated_logic.py",
    "test_url_variants.py", "test_urls.py", "test_user_request_validation.py", "test_with_logs.py",
    "test_work_item_210636.py", "test_work_item_215042.py"
)

foreach ($file in $testFiles) {
    if (Test-Path $file) {
        Move-Item $file "DELETE\test_scripts\"
        Write-Host "Перемещен: $file"
    }
}

# 4. Неиспользуемые сервисы
Write-Host "Перемещаем неиспользуемые сервисы..."
if (Test-Path "app\services\optimized_checklist_service.py") { 
    Move-Item "app\services\optimized_checklist_service.py" "DELETE\unused_services\" 
}
if (Test-Path "app\analyzers\documentation_analyzer.py") { 
    Move-Item "app\analyzers\documentation_analyzer.py" "DELETE\unused_services\" 
}
if (Test-Path "app\extractors\github_extractor.py") { 
    Move-Item "app\extractors\github_extractor.py" "DELETE\unused_services\" 
}
if (Test-Path "app\extractors\tfs_extractor.py") { 
    Move-Item "app\extractors\tfs_extractor.py" "DELETE\unused_services\" 
}

# 5. Неиспользуемые API
Write-Host "Перемещаем неиспользуемые API..."
if (Test-Path "app\api\advanced_endpoints.py") { 
    Move-Item "app\api\advanced_endpoints.py" "DELETE\unused_api\" 
}
if (Test-Path "app\api\extended_endpoints.py") { 
    Move-Item "app\api\extended_endpoints.py" "DELETE\unused_api\" 
}
if (Test-Path "app\api\tfs_routes.py") { 
    Move-Item "app\api\tfs_routes.py" "DELETE\unused_api\" 
}

# 6. Неиспользуемые модели
Write-Host "Перемещаем неиспользуемые модели..."
if (Test-Path "app\models\extended_models.py") { 
    Move-Item "app\models\extended_models.py" "DELETE\unused_models\" 
}
if (Test-Path "app\models\link_types.py") { 
    Move-Item "app\models\link_types.py" "DELETE\unused_models\" 
}

# 7. Неиспользуемые core модули
Write-Host "Перемещаем неиспользуемые core модули..."
if (Test-Path "app\core\extension_manager.py") { 
    Move-Item "app\core\extension_manager.py" "DELETE\unused_core\" 
}
if (Test-Path "app\core\interfaces.py") { 
    Move-Item "app\core\interfaces.py" "DELETE\unused_core\" 
}

# 8. Документация
Write-Host "Перемещаем документацию..."
$docFiles = @(
    "CHANGE_CHAIN_FIX_REPORT.md", "CONFLUENCE_CONNECTION_REPORT.md", "FINAL_FIX_REPORT.md",
    "IMPLEMENTATION_SUMMARY.md", "LOGIC_ANALYSIS_REPORT.md", "LOGIC_FIXES_PROPOSAL.md",
    "OPTIMIZATION_NOTES.md", "PERFORMANCE_ANALYSIS_REPORT.md", "PERFORMANCE_OPTIMIZATION_SUMMARY.md",
    "PROJECT_AUDIT_REPORT.md", "QUICK_START.md", "README_TFS.md"
)

foreach ($file in $docFiles) {
    if (Test-Path $file) {
        Move-Item $file "DELETE\documentation\"
        Write-Host "Перемещен: $file"
    }
}

# 9. Утилиты
Write-Host "Перемещаем утилиты..."
if (Test-Path "alternative_search.py") { Move-Item "alternative_search.py" "DELETE\utilities\" }
if (Test-Path "fix_async_tests.py") { Move-Item "fix_async_tests.py" "DELETE\utilities\" }

# 10. Docker файлы
Write-Host "Перемещаем Docker файлы..."
if (Test-Path "docker-compose.yml") { Move-Item "docker-compose.yml" "DELETE\docker_files\" }
if (Test-Path "Dockerfile") { Move-Item "Dockerfile" "DELETE\docker_files\" }
if (Test-Path "nginx.conf") { Move-Item "nginx.conf" "DELETE\docker_files\" }

Write-Host "Перемещение файлов завершено!"
Write-Host "Проверяем содержимое каталога DELETE:"
Get-ChildItem -Recurse DELETE | Select-Object Name, Directory
