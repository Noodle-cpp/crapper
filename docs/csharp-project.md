# C# / .NET project layout for crapper

Short checklist for **CC**, **coverage**, **CRAP**, and `.metrics/crap.edn`.

## Solution layout

- **Production** `.csproj` projects with `.cs` sources.
- A separate **test** `.csproj` named `*Tests.csproj` / `*.Tests.csproj`, or marked `<IsTestProject>true</IsTestProject>`.
- **ProjectReference** from the test project to the libraries crapper analyzes.

Crapper runs `dotnet test` on matching test projects, not on every library `.csproj`.

## Coverage

Add **`coverlet.collector`** to the test project. Default run:

```text
dotnet test <Tests.csproj> --collect:XPlat Code Coverage
```

Reports: `target/coverage/csharp/**/coverage.cobertura.xml`.

MSBuild Coverlet (`/p:CollectCoverage=true`) requires `--coverage-command`.

## Snapshot rules

Scored: methods with `{ }` or `=>` bodies; namespaces `Ns.Type` / `Ns.Outer.Inner`.

Skipped: constructors, property accessors, lambdas/local functions as separate entries; `*Tests.cs`; generated `*.Designer.cs`, `*.g.cs`, `*.generated.cs`.

## Running crapper

```bash
./crapper --root /path/to/solution
```

Use `--no-coverage`, `--use-existing-coverage`, or `--coverage-command` as needed.

Requires **`dotnet`** on PATH.

---

[Russian version](csharp-project.ru.md)
