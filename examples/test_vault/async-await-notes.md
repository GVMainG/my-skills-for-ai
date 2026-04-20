---
created: 2026-04-10T09:00:00
tags:
  - it/csharp
  - it/многопоточность
---

# Async/Await в C#

Разобрался с async/await и Task.Run(). ConfigureAwait(false) нужен для library кода.

## Основные концепты

При использовании async/await важно понимать как работает планировщик задач в .NET.

CancellationToken позволяет отменить длительную операцию.

```csharp
public async Task<string> GetDataAsync(CancellationToken ct)
{
    await Task.Delay(1000, ct);
    return "result";
}
```

## Производительность

Использование `ConfigureAwait(false)` в библиотечном коде помогает избежать deadlock.

Ссылки:
- [[SOLID Principles]]
- [[C# Advanced Topics]]
