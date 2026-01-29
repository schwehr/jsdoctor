from typing import Iterable, Sequence


def IsPrototypeProperty(namespace: str) -> bool:
  parts = GetNamespaceParts(namespace)
  return len(parts) >= 3 and parts[-2] == 'prototype'


def GetNamespaceFromParts(parts: list[str]) -> str:
  return '.'.join(parts)


def GetNamespaceParts(namespace: str) -> list[str]:
  # TODO(nanaze): Memoize. This is idempotent and hit a lot.
  return namespace.split('.')


def GetPrototypeProperty(namespace: str) -> str:
  assert IsPrototypeProperty(namespace)
  parts = namespace.split('.')
  return parts[-1]


def IsSymbolPartOfNamespace(symbol: str, namespace: str) -> bool:
  namespace_parts = GetNamespaceParts(namespace)
  symbol_parts = GetNamespaceParts(symbol)

  return namespace_parts == symbol_parts[0:len(namespace_parts)]


def _GetSymbolPartsInNamespace(
    symbol_parts: Sequence[str],
    namespace_parts: Sequence[str]
  ) -> int:
  # A symbol can't be shorter than its namespace.
  if len(symbol_parts) < len(namespace_parts):
    return 0

  count = 0
  while count < len(namespace_parts):
    if symbol_parts[count] != namespace_parts[count]:
      return count

    count += 1

  return count

def GetClosestNamespaceForSymbol(
    symbol: str,
    candidate_namespaces: Iterable[str]
) -> str | None:
  closest_namespace = None
  symbol_parts = GetNamespaceParts(symbol)

  max_count = 0

  valid_namespaces = list(filter(
    lambda ns: IsSymbolPartOfNamespace(symbol, ns), candidate_namespaces))

  for ns in valid_namespaces:
    namespace_parts = GetNamespaceParts(ns)
    count = _GetSymbolPartsInNamespace(symbol_parts, namespace_parts)

    if count > max_count:
      closest_namespace = ns
      max_count = count

  return closest_namespace
