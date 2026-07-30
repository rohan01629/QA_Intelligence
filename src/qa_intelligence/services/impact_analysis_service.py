"""ImpactAnalysisService — extract implementation signals from relevant source files."""

from __future__ import annotations

import re

import structlog

from qa_intelligence.domain.models.code_intelligence import (
    AffectedApi,
    AffectedFile,
    CodeArtifactRole,
    CodeSignal,
)

logger = structlog.get_logger(__name__)

_API_ROUTE_RE = re.compile(
    r"""(?ix)
    (?:
        \[(Http(Get|Post|Put|Patch|Delete)(?:Attribute)?)(?:\("([^"]+)"\))?\]
      | @app\.(get|post|put|patch|delete)\(\s*['"]([^'"]+)['"]
      | router\.(get|post|put|patch|delete)\(\s*['"]([^'"]+)['"]
      | (?:app|router)\.(get|post|put|patch|delete)\(\s*['"]([^'"]+)['"]
      | ['"](GET|POST|PUT|PATCH|DELETE)\s+(/[^'"]+)['"]
      | (fetch|axios)\(\s*['"`]([^'"`]+)['"`]
    )
    """
)

_VALIDATION_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)max(?:imum)?\s*(?:length|len)\s*[=:( ]\s*(\d+)"),
    re.compile(r"(?i)MinLength\((\d+)\)"),
    re.compile(r"(?i)MaxLength\((\d+)\)"),
    re.compile(r"(?i)required|NotNull|NotEmpty|IsRequired"),
    re.compile(r"(?i)duplicate|already\s+exists|unique"),
    re.compile(r"(?i)trim(?:\(|ming)?|Strip\("),
    re.compile(r"(?i)string\.IsNullOrWhiteSpace|isnullorwhitespace"),
)

_PERMISSION_RE = re.compile(
    r"(?i)Authorize|permission|role|IsInRole|can[A-Z]\w+|RequireClaim|Policy\("
)
_FEATURE_FLAG_RE = re.compile(
    r"(?i)feature[_-]?flag|LaunchDarkly|IsEnabled\(|FeatureToggle|unleash"
)
_DB_RE = re.compile(
    r"(?i)DbContext|SaveChanges|repository\.|INSERT |UPDATE |DELETE FROM|EntityFramework|mongoose|prisma|sqlalchemy"
)
_INTEGRATION_RE = re.compile(
    r"(?i)HttpClient|RestClient|webhook|ServiceBus|Kafka|RabbitMq|grpc|SendGrid|Stripe"
)
_ERROR_RE = re.compile(
    r"(?i)throw new |catch\s*\(|BadRequest|NotFound|Conflict|ProblemDetails|HttpException|raise "
)


class ImpactAnalysisService:
    """Analyze file contents and produce APIs, rules, and regression signals."""

    def analyze(
        self,
        files: list[AffectedFile],
        contents: dict[str, str],
        *,
        feature_name: str,
    ) -> dict[str, object]:
        apis: list[AffectedApi] = []
        business_rules: list[str] = []
        validation_rules: list[str] = []
        permissions: list[str] = []
        feature_flags: list[str] = []
        integrations: list[str] = []
        error_handling: list[str] = []
        database_interactions: list[str] = []
        ui_components: list[str] = []
        signals: list[CodeSignal] = []
        regression_areas: list[str] = []

        seen_apis: set[str] = set()
        seen_rules: set[str] = set()

        for item in files:
            text = contents.get(item.path, "")
            if not text:
                continue

            for api in self._extract_apis(item.path, text):
                key = f"{api.method.upper()} {api.path}"
                if key not in seen_apis:
                    seen_apis.add(key)
                    apis.append(api)

            for rule in self._extract_validation_rules(text):
                if rule not in seen_rules:
                    seen_rules.add(rule)
                    validation_rules.append(rule)
                    business_rules.append(rule)
                    signals.append(
                        CodeSignal(
                            kind="validation",
                            description=rule,
                            source_file=item.path,
                        )
                    )

            if _PERMISSION_RE.search(text):
                msg = f"Permission/authorization checks in {item.path}"
                permissions.append(msg)
                signals.append(
                    CodeSignal(kind="permission", description=msg, source_file=item.path)
                )
            if _FEATURE_FLAG_RE.search(text):
                msg = f"Feature flag usage in {item.path}"
                feature_flags.append(msg)
                signals.append(
                    CodeSignal(kind="feature_flag", description=msg, source_file=item.path)
                )
            if _DB_RE.search(text):
                msg = f"Database / persistence interaction in {item.path}"
                database_interactions.append(msg)
                signals.append(
                    CodeSignal(kind="database", description=msg, source_file=item.path)
                )
            if _INTEGRATION_RE.search(text):
                msg = f"External integration in {item.path}"
                integrations.append(msg)
                signals.append(
                    CodeSignal(kind="integration", description=msg, source_file=item.path)
                )
            if _ERROR_RE.search(text):
                msg = f"Explicit error handling in {item.path}"
                error_handling.append(msg)
                signals.append(
                    CodeSignal(kind="error_handling", description=msg, source_file=item.path)
                )

            if item.role in {
                CodeArtifactRole.COMPONENT,
                CodeArtifactRole.PAGE,
            } or item.path.endswith((".tsx", ".jsx", ".vue")):
                ui_components.append(item.path)
                stem = PathStem(item.path)
                if stem:
                    regression_areas.append(stem)

            if item.role in {
                CodeArtifactRole.SERVICE,
                CodeArtifactRole.REPOSITORY,
                CodeArtifactRole.HANDLER,
                CodeArtifactRole.COMMAND,
            }:
                stem = PathStem(item.path)
                if stem:
                    regression_areas.append(stem)

        # Always include feature-named regression area.
        if feature_name.strip():
            regression_areas.insert(0, feature_name.strip())

        # Deduplicate regression areas preserving order.
        regression_areas = _unique(regression_areas)

        result = {
            "affected_apis": apis,
            "business_rules": _unique(business_rules),
            "validation_rules": _unique(validation_rules),
            "permissions": _unique(permissions),
            "feature_flags": _unique(feature_flags),
            "integrations": _unique(integrations),
            "error_handling": _unique(error_handling),
            "database_interactions": _unique(database_interactions),
            "ui_components": _unique(ui_components),
            "signals": signals,
            "regression_areas": regression_areas,
        }
        logger.info(
            "code_intel.impact_analyzed",
            files=len(files),
            apis=len(apis),
            validation_rules=len(validation_rules),
            signals=len(signals),
        )
        return result

    def _extract_apis(self, source_file: str, text: str) -> list[AffectedApi]:
        apis: list[AffectedApi] = []
        for match in _API_ROUTE_RE.finditer(text):
            groups = [g for g in match.groups() if g]
            method = ""
            path = ""
            joined = " ".join(groups)
            method_match = re.search(
                r"(?i)\b(GET|POST|PUT|PATCH|DELETE|HttpGet|HttpPost|HttpPut|HttpPatch|HttpDelete)\b",
                joined,
            )
            if method_match:
                raw = method_match.group(1)
                method = raw.replace("Http", "").upper()
            path_match = re.search(r"(/[A-Za-z0-9_{}\-./]+)", joined)
            if path_match:
                path = path_match.group(1)
            elif groups:
                # fetch/axios URL may be relative without leading analysis
                candidate = groups[-1]
                if candidate.startswith("/") or "://" in candidate or "{" in candidate:
                    path = candidate
            if not path:
                continue
            apis.append(
                AffectedApi(
                    method=method or "ANY",
                    path=path,
                    source_file=source_file,
                )
            )
        return apis

    def _extract_validation_rules(self, text: str) -> list[str]:
        rules: list[str] = []
        if re.search(r"(?i)duplicate|already\s+exists|unique", text):
            rules.append("Duplicate values are not allowed")
        if re.search(r"(?i)trim|Strip\(|IsNullOrWhiteSpace", text):
            rules.append("Leading/trailing whitespace is trimmed or rejected")
        for match in re.finditer(r"(?i)MaxLength\((\d+)\)", text):
            rules.append(f"Maximum length is {match.group(1)}")
        for match in re.finditer(r"(?i)max(?:imum)?\s*(?:length|len)\s*[=:( ]\s*(\d+)", text):
            rules.append(f"Maximum length is {match.group(1)}")
        for match in re.finditer(r"(?i)MinLength\((\d+)\)", text):
            rules.append(f"Minimum length is {match.group(1)}")
        if re.search(r"(?i)\[Required\]|NotNull|NotEmpty|IsRequired|required:\s*true", text):
            rules.append("Required fields must be provided")
        return rules


def PathStem(path: str) -> str:
    name = path.replace("\\", "/").rsplit("/", 1)[-1]
    if "." in name:
        name = name.rsplit(".", 1)[0]
    # Split PascalCase / camelCase lightly.
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    return spaced.replace("_", " ").replace("-", " ").strip()


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = value.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(value.strip())
    return out
