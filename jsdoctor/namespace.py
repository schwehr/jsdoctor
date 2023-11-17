def IsPrototypeProperty(namespace):
  parts = GetNamespaceParts(namespace)
  return len(parts) >= 3 and parts[-2] == 'prototype'

def GetNamesapceFromParts(parts):
  return '.'.join(parts)

def GetNamespaceParts(namespace):
  # TODO(nanaze): Memoize. This is idempotent and hit a lot.
  return namespace.split('.')

def GetPrototypeProperty(namespace):
  assert IsPrototypeProperty(namespace)
  parts = namespace.split('.')
  return parts[-1]

def IsSymbolPartOfNamespace(symbol, namespace):
  namespace_parts = GetNamespaceParts(namespace)
  symbol_parts = GetNamespaceParts(symbol)

  return (
    namespace_parts ==
    symbol_parts[0:len(namespace_parts)])

def _GetSymbolPartsInNamespace(symbol_parts, namespace_parts):
  # A symbol can't be shorter than its namespace.
  if len(symbol_parts) < len(namespace_parts):
    return 0

  count = 0
  while count < len(namespace_parts):
    if symbol_parts[count] != namespace_parts[count]:
      return count

    count += 1

  return count

def GetClosestNamespaceForSymbol(symbol, candidate_namespaces):
  closest_namespace = None
  symbol_parts = GetNamespaceParts(symbol)

  max_count = 0

  valid_namespaces = filter(
    lambda ns: IsSymbolPartOfNamespace(symbol, ns), candidate_namespaces)

  for ns in valid_namespaces:
    namespace_parts = GetNamespaceParts(ns)
    count = _GetSymbolPartsInNamespace(symbol_parts, namespace_parts)

    if count > max_count:
      closest_namespace = ns
      max_count = count

  return closest_namespace
