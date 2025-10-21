# Техническое решение: Novabev. Переименование полей в Ч-Web

## Обзор решения

### Проблема
Клиент Novabev при переходе с клиента Чикаго на Чикаго Web теряет возможность использования индивидуальных названий полей (например, "Код" для ТТ = "Код SY"). Требуется реализовать систему переименования полей, которая будет сохранять настройки при обновлениях системы.

### Цель решения
Создать гибкую систему локализации полей справочников, которая позволит:
- Переименовывать поля для конкретных тенантов
- Сохранять настройки при обновлениях системы
- Обеспечивать изоляцию между клиентами
- Поддерживать множественные языки

## Архитектура решения

### Общая схема
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Файлы         │    │   Система       │    │   Пользователь  │
│   переводов     │    │   локализации   │    │   интерфейс     │
│                 │    │                 │    │                 │
│ - ru-RU.json    │───►│ - Entities      │───►│ - Переименованные│
│ - en-US.json    │    │   Columns       │    │   поля          │
│ - tenant config │    │   Dictionary    │    │ - Сохранение    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Компоненты системы

#### 1. Файловая система переводов
```
libs/lib-apps-shared/src/lib/locale/tenants/<Brand>/
├── ru-RU.json          # Русские переводы
├── en-US.json          # Английские переводы
└── tenant-config.json  # Конфигурация тенанта
```

#### 2. Система локализации
- **EntitiesColumnsDictionary**: Словарь переименований полей
- **TranslationLoader**: Загрузчик файлов переводов
- **TenantResolver**: Определение текущего тенанта
- **FieldNameResolver**: Резолвер названий полей

#### 3. Пользовательский интерфейс
- **Grid Headers**: Заголовки таблиц с переименованными полями
- **Form Labels**: Метки полей в формах
- **Settings Panel**: Панель настроек переводов

## Детальная реализация

### 1. Структура файлов переводов

#### Формат ru-RU.json
```json
{
  "outlets": {
    "code": "Код SY",
    "name": "Наименование ТТ",
    "address": "Адрес размещения"
  },
  "goods": {
    "name": "Название товара",
    "article": "Артикул",
    "price": "Цена продажи"
  },
  "counteragents": {
    "inn": "ИНН/КПП",
    "name": "Наименование организации",
    "contactPerson": "Контактное лицо"
  }
}
```

#### Формат en-US.json
```json
{
  "outlets": {
    "code": "Code SY",
    "name": "Outlet Name",
    "address": "Location Address"
  },
  "goods": {
    "name": "Product Name",
    "article": "Article",
    "price": "Sale Price"
  },
  "counteragents": {
    "inn": "Tax ID",
    "name": "Organization Name",
    "contactPerson": "Contact Person"
  }
}
```

### 2. TypeScript интерфейсы

#### Интерфейс для переводов
```typescript
interface FieldTranslations {
  [entityName: string]: {
    [fieldName: string]: string;
  };
}

interface TenantConfig {
  brand: string;
  locale: string;
  translations: FieldTranslations;
}
```

#### Сервис локализации
```typescript
@Injectable()
export class FieldLocalizationService {
  private translations: FieldTranslations = {};
  private currentTenant: string = '';

  constructor(
    private http: HttpClient,
    private tenantResolver: TenantResolver
  ) {
    this.loadTranslations();
  }

  /**
   * Получает локализованное название поля
   */
  getFieldName(entityName: string, fieldName: string): string {
    const tenantTranslations = this.translations[this.currentTenant];
    
    if (tenantTranslations?.[entityName]?.[fieldName]) {
      return tenantTranslations[entityName][fieldName];
    }
    
    // Fallback на стандартное название
    return this.getDefaultFieldName(entityName, fieldName);
  }

  /**
   * Загружает переводы для текущего тенанта
   */
  private async loadTranslations(): Promise<void> {
    try {
      this.currentTenant = this.tenantResolver.getCurrentTenant();
      const translations = await this.http.get<FieldTranslations>(
        `assets/locale/tenants/${this.currentTenant}/ru-RU.json`
      ).toPromise();
      
      this.translations[this.currentTenant] = translations;
    } catch (error) {
      console.warn('Failed to load tenant translations:', error);
    }
  }

  /**
   * Получает стандартное название поля
   */
  private getDefaultFieldName(entityName: string, fieldName: string): string {
    const defaultTranslations = {
      outlets: {
        code: 'Код',
        name: 'Наименование',
        address: 'Адрес'
      },
      goods: {
        name: 'Наименование',
        article: 'Артикул',
        price: 'Цена'
      }
    };
    
    return defaultTranslations[entityName]?.[fieldName] || fieldName;
  }
}
```

### 3. Angular компоненты

#### Компонент таблицы с локализованными заголовками
```typescript
@Component({
  selector: 'app-localized-grid',
  template: `
    <table>
      <thead>
        <tr>
          <th *ngFor="let column of columns">
            {{ getLocalizedHeader(column) }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr *ngFor="let row of data">
          <td *ngFor="let column of columns">
            {{ row[column.field] }}
          </td>
        </tr>
      </tbody>
    </table>
  `
})
export class LocalizedGridComponent {
  @Input() columns: GridColumn[] = [];
  @Input() data: any[] = [];

  constructor(
    private fieldLocalization: FieldLocalizationService
  ) {}

  getLocalizedHeader(column: GridColumn): string {
    return this.fieldLocalization.getFieldName(
      column.entityName, 
      column.fieldName
    );
  }
}
```

#### Сервис для работы с тенантами
```typescript
@Injectable()
export class TenantResolver {
  private currentTenant: string = '';

  constructor(
    private router: Router,
    private activatedRoute: ActivatedRoute
  ) {
    this.resolveTenant();
  }

  getCurrentTenant(): string {
    return this.currentTenant;
  }

  private resolveTenant(): void {
    // Получение тенанта из URL или конфигурации
    this.activatedRoute.params.subscribe(params => {
      this.currentTenant = params['tenant'] || 'default';
    });
  }
}
```

### 4. Конфигурация системы

#### Конфигурационный файл
```typescript
export const LOCALIZATION_CONFIG = {
  defaultLocale: 'ru-RU',
  supportedLocales: ['ru-RU', 'en-US'],
  tenantPath: 'assets/locale/tenants',
  fallbackEnabled: true,
  cacheEnabled: true,
  cacheTimeout: 300000 // 5 минут
};
```

#### Модуль локализации
```typescript
@NgModule({
  imports: [
    HttpClientModule,
    RouterModule
  ],
  providers: [
    FieldLocalizationService,
    TenantResolver,
    { provide: 'LOCALIZATION_CONFIG', useValue: LOCALIZATION_CONFIG }
  ]
})
export class LocalizationModule { }
```

### 5. HTTP сервис для загрузки переводов

```typescript
@Injectable()
export class TranslationLoaderService {
  private cache = new Map<string, FieldTranslations>();

  constructor(private http: HttpClient) {}

  async loadTranslations(tenant: string, locale: string): Promise<FieldTranslations> {
    const cacheKey = `${tenant}-${locale}`;
    
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey)!;
    }

    try {
      const translations = await this.http.get<FieldTranslations>(
        `assets/locale/tenants/${tenant}/${locale}.json`
      ).toPromise();
      
      this.cache.set(cacheKey, translations);
      return translations;
    } catch (error) {
      console.error(`Failed to load translations for ${tenant}/${locale}:`, error);
      return {};
    }
  }

  clearCache(): void {
    this.cache.clear();
  }
}
```

## Интеграция с существующей системой

### 1. Обновление компонентов таблиц

#### Базовый компонент таблицы
```typescript
@Component({
  selector: 'app-base-grid',
  template: `
    <div class="grid-container">
      <table class="data-grid">
        <thead>
          <tr>
            <th *ngFor="let column of columns" 
                [class]="column.cssClass">
              {{ getColumnHeader(column) }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let row of data; trackBy: trackByFn">
            <td *ngFor="let column of columns" 
                [class]="column.cssClass">
              <ng-container [ngSwitch]="column.type">
                <span *ngSwitchCase="'text'">{{ row[column.field] }}</span>
                <span *ngSwitchCase="'number'">{{ row[column.field] | number }}</span>
                <span *ngSwitchCase="'date'">{{ row[column.field] | date }}</span>
                <span *ngSwitchDefault>{{ row[column.field] }}</span>
              </ng-container>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  `
})
export class BaseGridComponent {
  @Input() columns: GridColumn[] = [];
  @Input() data: any[] = [];

  constructor(
    private fieldLocalization: FieldLocalizationService
  ) {}

  getColumnHeader(column: GridColumn): string {
    if (column.localized) {
      return this.fieldLocalization.getFieldName(
        column.entityName, 
        column.fieldName
      );
    }
    return column.title || column.fieldName;
  }

  trackByFn(index: number, item: any): any {
    return item.id || index;
  }
}
```

### 2. Обновление форм

#### Компонент формы с локализованными метками
```typescript
@Component({
  selector: 'app-localized-form',
  template: `
    <form [formGroup]="form">
      <div *ngFor="let field of formFields" class="form-field">
        <label [for]="field.name">
          {{ getFieldLabel(field) }}
        </label>
        <input 
          [id]="field.name"
          [formControlName]="field.name"
          [type]="field.type"
          [placeholder]="getFieldPlaceholder(field)">
        <div *ngIf="form.get(field.name)?.invalid && form.get(field.name)?.touched" 
             class="error-message">
          {{ getFieldError(field) }}
        </div>
      </div>
    </form>
  `
})
export class LocalizedFormComponent {
  @Input() form: FormGroup;
  @Input() formFields: FormField[] = [];

  constructor(
    private fieldLocalization: FieldLocalizationService
  ) {}

  getFieldLabel(field: FormField): string {
    if (field.localized) {
      return this.fieldLocalization.getFieldName(
        field.entityName, 
        field.fieldName
      );
    }
    return field.label || field.name;
  }

  getFieldPlaceholder(field: FormField): string {
    return field.placeholder || this.getFieldLabel(field);
  }

  getFieldError(field: FormField): string {
    const control = this.form.get(field.name);
    if (control?.errors) {
      const firstError = Object.keys(control.errors)[0];
      return this.getErrorMessage(field, firstError);
    }
    return '';
  }

  private getErrorMessage(field: FormField, errorType: string): string {
    const errorMessages = {
      required: `${this.getFieldLabel(field)} обязателен для заполнения`,
      minlength: `Минимальная длина ${field.minLength} символов`,
      maxlength: `Максимальная длина ${field.maxLength} символов`,
      email: 'Некорректный формат email',
      pattern: 'Некорректный формат данных'
    };
    
    return errorMessages[errorType] || 'Ошибка валидации';
  }
}
```

### 3. Сервис для работы с конфигурацией

```typescript
@Injectable()
export class LocalizationConfigService {
  private config: LocalizationConfig;

  constructor(
    @Inject('LOCALIZATION_CONFIG') config: LocalizationConfig
  ) {
    this.config = config;
  }

  getConfig(): LocalizationConfig {
    return this.config;
  }

  getTenantPath(tenant: string): string {
    return `${this.config.tenantPath}/${tenant}`;
  }

  getTranslationPath(tenant: string, locale: string): string {
    return `${this.getTenantPath(tenant)}/${locale}.json`;
  }

  isLocaleSupported(locale: string): boolean {
    return this.config.supportedLocales.includes(locale);
  }

  getDefaultLocale(): string {
    return this.config.defaultLocale;
  }
}
```

## Обработка ошибок

### 1. Обработка ошибок загрузки переводов

```typescript
@Injectable()
export class TranslationErrorHandler {
  constructor(
    private notificationService: NotificationService,
    private logger: LoggerService
  ) {}

  handleTranslationError(error: any, tenant: string, locale: string): void {
    this.logger.error('Translation loading failed', {
      tenant,
      locale,
      error: error.message
    });

    this.notificationService.showWarning(
      `Не удалось загрузить переводы для ${tenant}. Используются стандартные названия полей.`
    );
  }

  handleMissingTranslation(entityName: string, fieldName: string): void {
    this.logger.warn('Missing translation', {
      entityName,
      fieldName
    });
  }
}
```

### 2. Валидация файлов переводов

```typescript
@Injectable()
export class TranslationValidator {
  validateTranslationFile(translations: any): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    if (!translations || typeof translations !== 'object') {
      errors.push('Файл переводов должен содержать объект');
      return { valid: false, errors, warnings };
    }

    // Проверка структуры
    for (const [entityName, fields] of Object.entries(translations)) {
      if (typeof fields !== 'object') {
        errors.push(`Поля для сущности ${entityName} должны быть объектом`);
        continue;
      }

      for (const [fieldName, translation] of Object.entries(fields)) {
        if (typeof translation !== 'string') {
          errors.push(`Перевод для ${entityName}.${fieldName} должен быть строкой`);
        }

        if (translation.length === 0) {
          warnings.push(`Пустой перевод для ${entityName}.${fieldName}`);
        }
      }
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }
}
```

## Тестирование

### 1. Unit тесты

```typescript
describe('FieldLocalizationService', () => {
  let service: FieldLocalizationService;
  let httpMock: jasmine.SpyObj<HttpClient>;
  let tenantResolverMock: jasmine.SpyObj<TenantResolver>;

  beforeEach(() => {
    const httpSpy = jasmine.createSpyObj('HttpClient', ['get']);
    const tenantSpy = jasmine.createSpyObj('TenantResolver', ['getCurrentTenant']);

    TestBed.configureTestingModule({
      providers: [
        FieldLocalizationService,
        { provide: HttpClient, useValue: httpSpy },
        { provide: TenantResolver, useValue: tenantSpy }
      ]
    });

    service = TestBed.inject(FieldLocalizationService);
    httpMock = TestBed.inject(HttpClient) as jasmine.SpyObj<HttpClient>;
    tenantResolverMock = TestBed.inject(TenantResolver) as jasmine.SpyObj<TenantResolver>;
  });

  it('should return localized field name when translation exists', () => {
    // Arrange
    const translations = {
      outlets: { code: 'Код SY' }
    };
    httpMock.get.and.returnValue(of(translations));
    tenantResolverMock.getCurrentTenant.and.returnValue('novabev');

    // Act
    const result = service.getFieldName('outlets', 'code');

    // Assert
    expect(result).toBe('Код SY');
  });

  it('should return default field name when translation does not exist', () => {
    // Arrange
    httpMock.get.and.returnValue(throwError('Not found'));
    tenantResolverMock.getCurrentTenant.and.returnValue('novabev');

    // Act
    const result = service.getFieldName('outlets', 'code');

    // Assert
    expect(result).toBe('Код');
  });
});
```

### 2. Интеграционные тесты

```typescript
describe('LocalizedGridComponent Integration', () => {
  let component: LocalizedGridComponent;
  let fixture: ComponentFixture<LocalizedGridComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [LocalizedGridComponent],
      imports: [HttpClientTestingModule],
      providers: [
        FieldLocalizationService,
        TenantResolver
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(LocalizedGridComponent);
    component = fixture.componentInstance;
  });

  it('should display localized headers', () => {
    // Arrange
    component.columns = [
      { entityName: 'outlets', fieldName: 'code', title: 'Code' }
    ];
    component.data = [{ code: 'TT001' }];

    // Act
    fixture.detectChanges();

    // Assert
    const headerElement = fixture.debugElement.query(
      By.css('th')
    ).nativeElement;
    expect(headerElement.textContent.trim()).toBe('Код SY');
  });
});
```

## Производительность

### 1. Кэширование переводов

```typescript
@Injectable()
export class TranslationCacheService {
  private cache = new Map<string, FieldTranslations>();
  private cacheTimeout = 300000; // 5 минут

  set(tenant: string, locale: string, translations: FieldTranslations): void {
    const key = this.getCacheKey(tenant, locale);
    this.cache.set(key, {
      ...translations,
      _timestamp: Date.now()
    });
  }

  get(tenant: string, locale: string): FieldTranslations | null {
    const key = this.getCacheKey(tenant, locale);
    const cached = this.cache.get(key);
    
    if (!cached) {
      return null;
    }

    if (Date.now() - cached._timestamp > this.cacheTimeout) {
      this.cache.delete(key);
      return null;
    }

    return cached;
  }

  clear(): void {
    this.cache.clear();
  }

  private getCacheKey(tenant: string, locale: string): string {
    return `${tenant}-${locale}`;
  }
}
```

### 2. Ленивая загрузка переводов

```typescript
@Injectable()
export class LazyTranslationLoader {
  private loadingPromises = new Map<string, Promise<FieldTranslations>>();

  async loadTranslations(tenant: string, locale: string): Promise<FieldTranslations> {
    const key = `${tenant}-${locale}`;
    
    if (this.loadingPromises.has(key)) {
      return this.loadingPromises.get(key)!;
    }

    const promise = this.loadTranslationsInternal(tenant, locale);
    this.loadingPromises.set(key, promise);
    
    return promise;
  }

  private async loadTranslationsInternal(tenant: string, locale: string): Promise<FieldTranslations> {
    try {
      const response = await fetch(`assets/locale/tenants/${tenant}/${locale}.json`);
      const translations = await response.json();
      return translations;
    } catch (error) {
      console.error('Failed to load translations:', error);
      return {};
    } finally {
      this.loadingPromises.delete(`${tenant}-${locale}`);
    }
  }
}
```

## Мониторинг

### 1. Метрики производительности

```typescript
@Injectable()
export class LocalizationMetricsService {
  private metrics = {
    translationLoads: 0,
    cacheHits: 0,
    cacheMisses: 0,
    loadTime: 0
  };

  recordTranslationLoad(loadTime: number): void {
    this.metrics.translationLoads++;
    this.metrics.loadTime += loadTime;
  }

  recordCacheHit(): void {
    this.metrics.cacheHits++;
  }

  recordCacheMiss(): void {
    this.metrics.cacheMisses++;
  }

  getMetrics(): LocalizationMetrics {
    return {
      ...this.metrics,
      averageLoadTime: this.metrics.loadTime / this.metrics.translationLoads,
      cacheHitRate: this.metrics.cacheHits / (this.metrics.cacheHits + this.metrics.cacheMisses)
    };
  }
}
```

### 2. Логирование

```typescript
@Injectable()
export class LocalizationLogger {
  constructor(private logger: LoggerService) {}

  logTranslationLoad(tenant: string, locale: string, success: boolean, loadTime: number): void {
    this.logger.info('Translation load', {
      tenant,
      locale,
      success,
      loadTime,
      timestamp: new Date().toISOString()
    });
  }

  logMissingTranslation(entityName: string, fieldName: string, tenant: string): void {
    this.logger.warn('Missing translation', {
      entityName,
      fieldName,
      tenant,
      timestamp: new Date().toISOString()
    });
  }

  logCacheHit(tenant: string, locale: string): void {
    this.logger.debug('Translation cache hit', {
      tenant,
      locale,
      timestamp: new Date().toISOString()
    });
  }
}
```

## Заключение

### Ключевые особенности решения
1. **Гибкость**: Поддержка множественных тенантов и языков
2. **Производительность**: Кэширование и ленивая загрузка
3. **Надежность**: Обработка ошибок и fallback на стандартные названия
4. **Масштабируемость**: Легкое добавление новых сущностей и полей
5. **Совместимость**: Интеграция с существующей системой без breaking changes

### Преимущества
- **Пользовательский опыт**: Сохранение привычных названий полей
- **Административная гибкость**: Легкая настройка через файлы JSON
- **Техническая стабильность**: Сохранение настроек при обновлениях
- **Производительность**: Минимальное влияние на скорость работы

### Ограничения
- **ХП не изменяются**: Связанные процедуры используют оригинальные названия
- **Импорт данных**: Требует использования стандартных названий полей
- **API**: Внешние интерфейсы не затрагиваются

---
*Документ создан: 27.09.2025*  
*Версия: 1.0*  
*Статус: Готов к реализации*
