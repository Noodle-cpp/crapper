# C# / .NET проект для crapper

Краткий чеклист: что должно быть в репозитории, чтобы crapper считал **CC**, **покрытие** и **CRAP** и писал `.metrics/crap.edn`.

## Структура solution

| Что | Зачем |
|-----|--------|
| Один или несколько **production** `.csproj` (Application, Infrastructure, …) | Источники `.cs` для цикломатической сложности |
| Отдельный **test** `.csproj` | `dotnet test` и Cobertura; crapper **не** гоняет тесты по каждой библиотеке отдельно |
| Имя test-проекта `*Tests.csproj` / `*.Tests.csproj` **или** `<IsTestProject>true</IsTestProject>` | Так crapper находит test-проект |
| `<ProjectReference>` из test-проекта на анализируемые библиотеки | Crapper запускает coverage только для test-проектов, которые ссылаются на production из текущего прогона |

Типовая схема:

```text
src/
  MyApp.Application/
    MyApp.Application.csproj
    Services/...
  MyApp.Tests/
    MyApp.Tests.csproj      ← coverlet.collector, xUnit/NUnit/MSTest
    *Tests.cs               ← файлы тестов
```

Если test-проектов с подходящими ссылками нет, crapper fallback: `dotnet test` по production `.csproj` (обычно бесполезно).

## Покрытие (Coverlet)

Crapper по умолчанию:

```text
dotnet test <Tests.csproj> --collect:XPlat Code Coverage --results-directory=.../target/coverage/csharp/.../TestResults
```

В **test** `.csproj` нужен NuGet-пакет:

```xml
<PackageReference Include="coverlet.collector" Version="6.0.4">
  <PrivateAssets>all</PrivateAssets>
  <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
</PackageReference>
```

или:

```bash
dotnet add package coverlet.collector
```

Без `coverlet.collector` тесты могут пройти, но **`coverage.cobertura.xml` не появится** → crapper даст **0%** на методы.

Отчёт ищется под `target/coverage/csharp/**/coverage.cobertura.xml` и `**/TestResults/**/coverage.cobertura.xml`.

Альтернатива (MSBuild Coverlet) — только через свой `--coverage-command`; встроенный runner её не вызывает.

## Что попадает в `.metrics/crap.edn`

| В snapshot | Не в snapshot |
|------------|----------------|
| Методы с телом `{ ... }` или `=> ...` | Конструкторы |
| Namespace `Company.Product.Type` / `Company.Product.Outer.Inner` | Property get/set (accessors) |
| Имя метода = простое имя (`Place`, `RunAsync`) | Local functions, лямбды как отдельные записи |
| | Файлы `*Tests.cs`, `*Test.cs`, каталоги `test` / `tests` / … |
| | `*.Designer.cs`, `*.g.cs`, `*.generated.cs` |

Вложенный тип: в EDN **`Outer.Inner`**, в Cobertura класс **`Outer+Inner`** (crapper сопоставляет сам).

Перегрузки с одним именем — одна строка в EDN (как у Java).

## Контракт для uml-viewer (когда появится C# на диаграмме)

- `:namespace` в `crap.edn` = **`Namespace.Type`** (точки), как `:ns` класса на диаграмме.
- `:name` = имя метода на карточке класса.

## Запуск

Из корня solution (Windows):

```powershell
cd path\to\crapper
.\.venv\Scripts\python.exe -m crapper --root "D:\path\to\YourSolution"
```

| Флаг | Эффект |
|------|--------|
| `--no-coverage` | Только CC; `:coverage` и `:crap` = `nil` |
| `--use-existing-coverage` | Не вызывать `dotnet test`; читать Cobertura с диска |
| `--coverage-command "..."` | Своя команда вместо встроенной |
| `--changed` | Только изменённые по git `.cs` |

Нужны **`dotnet`** в PATH и успешная сборка test-проекта.

## Частые проблемы

1. **Вспомогательные `.cs` в test-проекте** (`GlpiTestHttp.cs` без суффикса `Tests`) сейчас могут попасть в CRAP — лучше держать хелперы в `*Tests.cs` или в каталоге, который вы исключаете из обхода (улучшение discover в работе).
2. **`dotnet test` с exit code ≠ 0** — crapper всё равно может прочитать Cobertura, но в stderr будет предупреждение; для стабильного CI почините падающие тесты.
3. **Локаль / culture** — не влияет на crapper, но ломает тесты и мешает coverage-run.

## Минимальный smoke-test

```powershell
dotnet list path\to\MyApp.Tests.csproj package | findstr coverlet
.\.venv\Scripts\python.exe -m crapper --root path\to\solution --no-coverage
# в crap.edn есть :namespace и :complexity

.\.venv\Scripts\python.exe -m crapper --root path\to\solution
# в crap.edn :coverage и :crap — числа, не nil
```

---

[English version](csharp-project.md)
