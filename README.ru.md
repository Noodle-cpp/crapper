# crapper

[English documentation](README.md)

CRAP-оценки для Clojure, Java, C#, Go, TypeScript, Rust и Python. Один запуск определяет язык каждого исходного файла, применяет правила сложности и покрытия для этого языка и записывает снимок, который уже читает [uml-viewer](https://github.com/unclebob/uml-viewer).

Формула — как в [crap4clj](https://github.com/unclebob/crap4clj), [crap4java](https://github.com/unclebob/crap4java) и [crap4go](https://github.com/unclebob/crap4go):

```text
CRAP = CC² × (1 − coverage)³ + CC
```

`CC` — цикломатическая сложность. `coverage` — доля функции, прогнанная тестами. Оценка 1–5 — низкий риск, 5–30 — стоит посмотреть, 30+ — сложно и слабо покрыто тестами.

## Запуск

```bash
./crapper
```

При первом запуске создаётся `.venv` и устанавливается инструмент. Из корня проекта обходится дерево, пропускаются `test`, `spec`, `vendor`, `node_modules` и `target`, записываются два результата:

- таблица в stdout, сначала худшие оценки
- `.metrics/crap.edn`, перезаписывается при каждом успешном анализе

```bash
./crapper --no-coverage                  # только сложность; покрытие N/A
./crapper --use-existing-coverage        # читать отчёты уже на диске
./crapper src/demo/core.clj src/ui       # эти файлы и деревья
./crapper --changed                      # добавления и правки по git
./crapper combat                         # фрагмент пути, как в crap4clj
./crapper --threshold 30                 # код выхода 2, если худшая оценка выше
```

## Снимок

`.metrics/crap.edn` имеет ту же форму, что пишет crap4clj:

```clojure
{:entries [{:name "place"
            :namespace "demo.Board"
            :complexity 3
            :coverage 75.0
            :crap 3.1}]}
```

uml-viewer группирует записи по `:namespace` и сопоставляет каждую операцию по `:name`. `nil` в coverage — результат `--no-coverage`: только сложность, CRAP тоже `nil`. Функция, не упомянутая в отчёте о покрытии, получает 0%.

| Язык | `:namespace` | `:name` |
| --- | --- | --- |
| Clojure | `ns` | имя `defn` / `defn-` |
| Java | `package.Class` или `package.Outer.Inner` | имя метода |
| C# | `namespace.Type` или `namespace.Outer.Inner` | имя метода |
| Go | путь импорта пакета или `import/path.Receiver` | имя функции или метода |
| TypeScript | точечный путь модуля или `module.Class` | имя функции или метода |
| Rust | `crate::module` или `crate::module::Type` | имя функции или метода |
| Python | точечный путь модуля или `module.Class` | имя функции или метода |

Переименование или перенос — новая запись. Сопоставления идентичности между запусками нет.

## Что считает каждый язык

Clojure следует crap4clj: `if` / `when` и варианты, `and`, `or`, `loop`, `catch`, каждая ветка `cond`, `condp`, `case`, `cond->`, `cond->>`, `some->`, `some->>`. Покрытие предпочитает построчные счётчики форм Cloverage, иначе LCOV.

Java следует crap4java: `if`, циклы, `catch`, `?:`, каждая метка `switch`, `&&` / `||`. Конструкторы и методы во внутренних классах не учитываются. Покрытие — счётчик `INSTRUCTION` JaCoCo.

C# — те же структурные решения, что у Java, плюс `??` и `?.`. Конструкторы, accessors свойств и методы внутри лямбд/local functions не учитываются. Вложенные типы: `namespace.Outer.Inner` в снимке, `namespace.Outer+Inner` в Cobertura. Expression-bodied методы учитываются. Покрытие — Cobertura (Coverlet) через `dotnet test` на test-проектах, которые ссылаются на анализируемые `.csproj` (имя `*Tests.csproj` или `<IsTestProject>true</IsTestProject>`); если таких нет — на сами библиотеки.

Go следует crap4go: `if`, `for`, `range`, каждая ветка `switch` и `select`, `&&` / `||`. Покрытие — `go test -coverprofile`.

TypeScript, TSX и JavaScript (`.js`, `.jsx`, `.mjs`, `.cjs`) используют те же структурные решения, что Java, включая `&&` в JSX, плюс `??` и `?.`. В записи попадают функции верхнего уровня, методы классов и стрелочные функции верхнего уровня. Inline-колбэк Express — `.get`, `.post`, `.put`, `.patch`, `.delete`, `.head`, `.options`, `.all`, `.use`, `.route(path).get(...)` — отдельная запись с именем `GET /users`. Второй колбэк на том же маршруте — `GET /users#2`. Его решения не дублируются во внешней функции. Остальные вложенные колбэки остаются внутри внешней функции. Покрытие — LCOV. При наличии веток (`BRDA`) внутри функции используются они; без веток — попадания по строкам. Скрипт `coverage` как есть. Vitest — `vitest --coverage` (при необходимости ставится `@vitest/coverage-v8` в `node_modules` без правки `package.json`). Другие тестовые скрипты оборачиваются в `c8`.

Rust считает `if`, циклы, каждое плечо `match`, `?`, `&&` / `||`. `mod tests` пропускается. Покрытие — LCOV из `cargo llvm-cov` или `cargo tarpaulin` в ближайшем каталоге с `Cargo.toml`. Если инструментов нет, ставится `cargo-llvm-cov`.

Python считает `if`, `elif`, `for`, `while`, `except`, каждый case `match`, фильтр comprehension, условное выражение, каждый `and` / `or`. Вложенные функции остаются во внешней. Покрытие — LCOV из `coverage.py`, pytest или `unittest`. `coverage` и `pytest` ставятся в интерпретатор проекта при отсутствии.

## Команды покрытия

По умолчанию перед измерением удаляется предыдущий отчёт для каждого языка и генерируется заново:

| Язык | Команда | Отчёт |
| --- | --- | --- |
| Clojure | `clj -M:cov --lcov` (нужны `deps.edn` или `bb.edn`) | `target/coverage/` |
| Java | JaCoCo Maven plugin `0.8.12` в каждом модуле с `pom.xml` | `target/site/jacoco/jacoco.xml` |
| Go | `go test ./... -coverprofile=...` | `target/coverage/go/coverage.out` |
| TypeScript | `npm run coverage`, или Vitest `--coverage`, или `npx c8 ... npm test` | `coverage/lcov.info` или `target/coverage/typescript/lcov.info` |
| Rust | `cargo llvm-cov` или `cargo tarpaulin`, по пакетам Cargo | `target/coverage/rust/lcov.info` |
| Python | `coverage run` с pytest или unittest, затем `coverage lcov` | `target/coverage/python/lcov.info` |
| C# | `dotnet test` с XPlat Code Coverage по test-проектам (`*Tests.csproj`, `IsTestProject`, ссылка на анализируемые библиотеки) | `target/coverage/csharp/**/coverage.cobertura.xml` |

Отсутствующий инструмент или упавшие тесты дают для языка 0% и всё равно пишут снимок. `--coverage-command` заменяет эти умолчания одной вашей командой. `--no-coverage` — запуск без покрытия и CRAP как N/A.

Требования к C# / .NET solution: [docs/csharp-project.ru.md](docs/csharp-project.ru.md).

## Разработка

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
```
