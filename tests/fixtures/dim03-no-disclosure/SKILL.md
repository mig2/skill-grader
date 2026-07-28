---
name: api-documenter
version: 1.0.0
author: example-team
tags: [documentation, api, openapi]
---

# API Documenter

## Description

Generate and maintain API documentation from source code. Use this skill when the user asks to document an API, generate OpenAPI specs, or produce reference documentation for HTTP endpoints. Trigger on phrasings like "document this API", "generate OpenAPI spec", "write API docs", or "create endpoint documentation". Do not trigger on requests to write code, test APIs, or produce user-facing guides.

## When to Use

**Trigger conditions:**
- "Document this API"
- "Generate an OpenAPI spec for …"
- "Write API reference docs for …"
- "Create endpoint documentation"
- "Produce a Swagger file for …"

**Do not trigger when:**
- The user asks to test the API (use api-tester skill)
- The user asks to write or modify the API implementation
- The user asks for user-facing how-to guides rather than reference docs

## Instructions

1. Identify all HTTP endpoints in the provided source code. Look for route decorators, router definitions, and handler functions. Common patterns include `@app.route`, `@router.get`, `app.get(`, `router.post(`, `@GetMapping`, `@PostMapping`, and similar framework-specific annotations.

2. For each endpoint, extract: HTTP method, path, path parameters, query parameters, request body schema, response schema, status codes, authentication requirements, and rate limiting notes if present.

3. Classify each endpoint by resource type. Group endpoints that operate on the same resource together. For example, `GET /users`, `POST /users`, `GET /users/{id}`, `PUT /users/{id}`, and `DELETE /users/{id}` should all appear under a `Users` section.

4. Identify the authentication scheme used by the API. Common schemes: API key (header or query param), Bearer token (OAuth 2.0 or JWT), Basic auth, HMAC signature. Document the scheme in a top-level `Authentication` section.

5. Extract error response schemas. Most APIs have a common error envelope. Document it once in an `Error Responses` section and reference it from individual endpoints rather than repeating it.

6. Determine the base URL and any environment-specific overrides (staging, production, sandbox). Document each environment.

7. Generate the OpenAPI 3.1 YAML output following the schema defined in the Output Contract section below.

8. Validate that the generated YAML is syntactically correct by reviewing it for proper indentation, quoting of special characters, and correct data types.

9. If the source code includes test files, scan them for usage examples. Convert any found examples into the `examples` field of the relevant operation object.

10. Write a short prose introduction (50–100 words) describing what the API does, who it is for, and what problems it solves. Place this in the `info.description` field.

## Authentication Schemes Reference

The following table describes how to document each authentication scheme in the OpenAPI `securitySchemes` object.

| Scheme | OpenAPI type | OpenAPI scheme | Notes |
|--------|-------------|----------------|-------|
| API key in header | `apiKey` | N/A | Set `in: header`, name the header |
| API key in query | `apiKey` | N/A | Set `in: query`, name the parameter |
| Bearer JWT | `http` | `bearer` | Set `bearerFormat: JWT` |
| Bearer OAuth 2.0 | `oauth2` | N/A | Define flows and scopes |
| Basic auth | `http` | `basic` | Warn that Basic is deprecated for new APIs |
| HMAC signature | `apiKey` | N/A | Document the signing algorithm in description |

## HTTP Status Code Reference

Document these status codes whenever they appear in the API. Include both the code and a short description so consumers know what to expect.

| Code | Name | When to use |
|------|------|-------------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST that creates a resource |
| 204 | No Content | Successful DELETE or action with no response body |
| 400 | Bad Request | Client sent invalid data; validation failed |
| 401 | Unauthorized | Missing or invalid authentication credentials |
| 403 | Forbidden | Valid credentials but insufficient permissions |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | State conflict (e.g., duplicate resource) |
| 422 | Unprocessable Entity | Request is well-formed but semantically invalid |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server-side failure |
| 503 | Service Unavailable | API is down or in maintenance mode |

## OpenAPI 3.1 Object Reference

The following describes each top-level object in an OpenAPI 3.1 document. Use this as a checklist when generating the spec.

### info object

Required fields: `title`, `version`. Recommended fields: `description`, `contact`, `license`, `termsOfService`.

- `title`: Short name of the API. Do not include "API" in the title if it is redundant.
- `version`: SemVer string of the API version being documented.
- `description`: Prose introduction. Supports Markdown.
- `contact.name`: Name of the team or person responsible.
- `contact.email`: Contact email for API support.
- `license.name`: SPDX identifier (e.g., `Apache-2.0`, `MIT`).

### servers object

List all environments. Each server has a `url` and an optional `description`. Use variables for environment-specific segments.

```yaml
servers:
  - url: https://api.example.com/v1
    description: Production
  - url: https://staging-api.example.com/v1
    description: Staging
  - url: http://localhost:8080/v1
    description: Local development
```

### paths object

Each path is a key. Each HTTP method under a path is an operation. Each operation has:

- `operationId`: Unique camelCase identifier. Format: `<verb><Resource>` e.g., `listUsers`, `createUser`, `getUserById`.
- `summary`: One-line description of what the operation does.
- `description`: Longer description if needed. Supports Markdown.
- `tags`: List of resource tags for grouping in documentation renderers.
- `parameters`: List of path, query, header, and cookie parameters.
- `requestBody`: Schema for the request body (POST, PUT, PATCH only).
- `responses`: Map of status codes to response objects.
- `security`: Override the global security requirement if this operation differs.

### components object

Place reusable schemas, responses, parameters, and security schemes here. Reference them from paths using `$ref`.

Always define the error envelope as a component:

```yaml
components:
  schemas:
    Error:
      type: object
      required: [code, message]
      properties:
        code:
          type: string
          description: Machine-readable error code.
        message:
          type: string
          description: Human-readable error description.
        details:
          type: array
          items:
            type: string
          description: Additional context. May be empty.
```

## Parameter Documentation Rules

Follow these rules for every parameter:

1. Path parameters are always required. Do not set `required: false` for path parameters.
2. Query parameters must include a `description` explaining what they filter or control.
3. If a query parameter accepts an enum, list all valid values in the `enum` field.
4. If a parameter has a default value, document it in `default`.
5. Avoid generic names like `data`, `payload`, or `body` for parameters. Use the resource name.
6. Date/time parameters must specify the format: `format: date-time` for ISO 8601 timestamps, `format: date` for date-only values.
7. Pagination parameters must always appear in pairs: `page` and `pageSize` (or `cursor` and `limit` for cursor-based pagination). Document the maximum allowed `pageSize`.

## Request Body Documentation Rules

1. Always specify `content` with at least `application/json`.
2. Provide an `example` for each request body.
3. Mark fields as `required` in the schema if the server will reject requests missing them.
4. Use `nullable: true` (OpenAPI 3.0 style) or `type: [string, null]` (OpenAPI 3.1 style) for optional fields that may be explicitly set to null.
5. Do not document internal fields that the client cannot set (e.g., `createdAt`, `id`).

## Response Documentation Rules

1. Every operation must document at least one 2xx response.
2. Every operation that accepts authentication must document 401.
3. Every operation that accepts a request body must document 400 or 422.
4. Document 404 for all operations on specific resources (those with `{id}` in the path).
5. If the API has a global rate limit, document 429 on all operations.
6. Response bodies must include a schema. Do not use `{}` or omit the schema.
7. Provide an example for each response body.

## Output Contract

Produce two outputs:

### Output 1: OpenAPI 3.1 YAML

A syntactically valid OpenAPI 3.1 YAML file. The file must:

- Begin with `openapi: "3.1.0"`
- Include `info`, `servers`, `paths`, and `components` top-level keys
- Have at least one path with at least one operation
- Pass validation against the OpenAPI 3.1 JSON Schema if a validator is available

### Output 2: Summary Report

A Markdown report in this format:

```markdown
# API Documentation Summary

**API name:** <title>
**Version:** <version>
**Endpoints documented:** <count>
**Authentication scheme:** <scheme name>

## Endpoints

| Method | Path | Operation ID | Summary |
|--------|------|-------------|---------|
| GET | /resource | listResources | List all resources |
| ... | ... | ... | ... |

## Gaps

<List any endpoints, parameters, or schemas that could not be fully documented due to missing information. Write "None identified" if complete.>
```

## Examples

**Example 1 — Flask REST API:**

Input: A Flask application with four routes: `GET /items`, `POST /items`, `GET /items/<id>`, `DELETE /items/<id>`, using JWT Bearer auth.

Expected output: OpenAPI 3.1 YAML with four operations under the `items` tag, JWT security scheme defined in components, 401 documented on all operations, 404 documented on the two `{id}` operations.

**Example 2 — Express.js API:**

Input: An Express.js router file with middleware-based auth and several nested routes.

Expected output: OpenAPI 3.1 YAML extracting routes from `router.get`, `router.post`, etc., with Bearer token auth inherited from middleware documented at the top level.

**Example 3 — Partial information:**

Input: Source code where the request body schema is not typed (e.g., `req.body` with no validation library).

Expected output: Schema documented as `type: object` with `additionalProperties: true`, and a gap note identifying that the schema could not be inferred.

## Environment and Portability

No scripts or external tools are required. This skill operates entirely on source code provided in context.

If the project has an existing OpenAPI spec, merge new endpoints into it rather than generating from scratch.

## Schema Type Mapping Reference

When inferring schemas from typed source code, use the following type mappings.

### Python Type Mappings

| Python type | OpenAPI type | OpenAPI format |
|-------------|-------------|----------------|
| `str` | `string` | — |
| `int` | `integer` | `int32` |
| `float` | `number` | `float` |
| `bool` | `boolean` | — |
| `datetime` | `string` | `date-time` |
| `date` | `string` | `date` |
| `UUID` | `string` | `uuid` |
| `bytes` | `string` | `byte` |
| `list[T]` | `array` | — (items: T) |
| `dict[str, T]` | `object` | — (additionalProperties: T) |
| `Optional[T]` | T | — (nullable: true) |
| `Literal["a","b"]` | `string` | — (enum: [a, b]) |

### TypeScript Type Mappings

| TypeScript type | OpenAPI type | OpenAPI format |
|----------------|-------------|----------------|
| `string` | `string` | — |
| `number` | `number` | — |
| `boolean` | `boolean` | — |
| `Date` | `string` | `date-time` |
| `string[]` | `array` | — (items: string) |
| `Record<string, T>` | `object` | — (additionalProperties: T) |
| `T \| null` | T | — (nullable: true) |
| `T \| undefined` | T | — (not required) |
| `"a" \| "b"` | `string` | — (enum: [a, b]) |

### Java/Kotlin Type Mappings

| Java/Kotlin type | OpenAPI type | OpenAPI format |
|-----------------|-------------|----------------|
| `String` | `string` | — |
| `Integer` / `int` | `integer` | `int32` |
| `Long` / `long` | `integer` | `int64` |
| `Double` / `double` | `number` | `double` |
| `Boolean` / `boolean` | `boolean` | — |
| `LocalDateTime` | `string` | `date-time` |
| `LocalDate` | `string` | `date` |
| `UUID` | `string` | `uuid` |
| `List<T>` | `array` | — (items: T) |
| `Map<String, T>` | `object` | — (additionalProperties: T) |

## Naming Conventions

Follow these naming conventions when generating `operationId` values, tag names, and schema names.

### Operation IDs

Operation IDs must be unique within the document and follow camelCase. Use this formula:

```
<verb><Resource><Qualifier?>
```

Where:
- `verb` is one of: `list`, `get`, `create`, `update`, `replace`, `delete`, `search`, `export`, `import`, `validate`, `send`, `process`, `generate`, `apply`
- `Resource` is the PascalCase name of the resource
- `Qualifier` is optional and used only when two operations on the same resource share the same verb (e.g., `listUsersByOrg`, `listUsersByRole`)

Examples:
- `GET /users` → `listUsers`
- `POST /users` → `createUser`
- `GET /users/{userId}` → `getUserById`
- `PUT /users/{userId}` → `replaceUser`
- `PATCH /users/{userId}` → `updateUser`
- `DELETE /users/{userId}` → `deleteUser`
- `GET /users/{userId}/roles` → `listUserRoles`
- `POST /users/{userId}/roles` → `assignUserRole`

### Tag Names

Tags must match the resource name in PascalCase with spaces permitted for multi-word resources. Examples:
- `Users`
- `API Keys`
- `Webhook Events`
- `Billing Invoices`

Do not use verbs in tag names. Tags represent resources, not actions.

### Schema Names

Schema names in `components/schemas` must:
- Be PascalCase
- Be the singular noun form of the resource (e.g., `User`, not `Users`)
- Use suffixes to distinguish variants:
  - `UserCreate` — request body for creating a user
  - `UserUpdate` — request body for updating a user (PATCH)
  - `UserResponse` — response body when returning a user
  - `UserListResponse` — response body when returning a list of users
  - `Error` — the error envelope

## Pagination Documentation

If the API supports pagination, document it consistently across all list endpoints.

### Offset Pagination

Offset pagination uses `page` (1-based) and `pageSize` parameters. The response envelope must include:

```yaml
components:
  schemas:
    PaginatedResponse:
      type: object
      required: [data, pagination]
      properties:
        data:
          type: array
          items: {}
          description: The page of results.
        pagination:
          type: object
          required: [page, pageSize, totalPages, totalItems]
          properties:
            page:
              type: integer
              description: Current page number (1-based).
            pageSize:
              type: integer
              description: Number of items per page.
            totalPages:
              type: integer
              description: Total number of pages available.
            totalItems:
              type: integer
              description: Total number of items across all pages.
```

Document `page` with a default of `1` and `pageSize` with a default and maximum. If the API does not document a maximum page size, note this as a gap.

### Cursor Pagination

Cursor pagination uses `cursor` and `limit` parameters. The response envelope must include:

```yaml
components:
  schemas:
    CursorPaginatedResponse:
      type: object
      required: [data, cursors]
      properties:
        data:
          type: array
          items: {}
          description: The page of results.
        cursors:
          type: object
          required: [next]
          properties:
            next:
              type: string
              nullable: true
              description: Cursor for the next page, or null if this is the last page.
            previous:
              type: string
              nullable: true
              description: Cursor for the previous page, or null if this is the first page.
```

Note in the description whether the cursor is opaque (do not attempt to parse) or structured.

## Webhook Documentation

If the API emits webhooks, document them in the `webhooks` top-level key (OpenAPI 3.1).

Each webhook entry has an event name and a path item describing the expected payload. Use this template:

```yaml
webhooks:
  userCreated:
    post:
      summary: User created event
      description: Emitted when a new user account is created.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [event, data, timestamp]
              properties:
                event:
                  type: string
                  enum: [user.created]
                data:
                  $ref: '#/components/schemas/UserResponse'
                timestamp:
                  type: string
                  format: date-time
      responses:
        "200":
          description: Webhook received successfully.
        "4XX":
          description: Webhook consumer returned an error. The API will retry.
```

If the API has a webhook signing secret, document it in the webhook's description and in a separate security guide section.

## Deprecation Documentation

When an endpoint or field is deprecated:

1. Set `deprecated: true` on the operation or schema property.
2. Add a `description` note explaining what to use instead and when the deprecated item will be removed.
3. If the API uses a `Sunset` header, document it in the response headers.

Template for deprecation notice in description:

```
**Deprecated.** Use `<replacement>` instead. This endpoint will be removed in version <version> on <date>.
```

## Rate Limiting Documentation

If the API enforces rate limits:

1. Document the 429 response on every operation subject to rate limiting.
2. In the 429 response, document the response headers used to communicate rate limit status:

```yaml
"429":
  description: Rate limit exceeded.
  headers:
    Retry-After:
      schema:
        type: integer
      description: Number of seconds to wait before retrying.
    X-RateLimit-Limit:
      schema:
        type: integer
      description: Maximum requests allowed in the current window.
    X-RateLimit-Remaining:
      schema:
        type: integer
      description: Requests remaining in the current window.
    X-RateLimit-Reset:
      schema:
        type: string
        format: date-time
      description: Time at which the rate limit window resets.
```

3. If rate limits differ by endpoint, document the specific limit in each operation's description.
4. If rate limits differ by authentication tier (free vs paid), document all tiers.

## Validation Rules Checklist

Before finalising the OpenAPI output, verify each of the following:

- [ ] All `$ref` values resolve to existing components.
- [ ] All `operationId` values are unique within the document.
- [ ] All path parameters in path templates have a corresponding `parameters` entry with `in: path`.
- [ ] All `required` arrays in schemas list fields that are also defined in `properties`.
- [ ] No schema uses both `nullable: true` and `type: [T, null]` (choose OpenAPI 3.0 or 3.1 style consistently).
- [ ] All `enum` values are of the correct type for the field.
- [ ] All `example` values match the schema they illustrate.
- [ ] The `info.version` string is a valid SemVer or follows the API's documented versioning scheme.
- [ ] All servers in the `servers` list have distinct `description` values.
- [ ] Any `security` requirement at operation level is defined in `components/securitySchemes`.

## Environment and Portability

No scripts or external tools are required. This skill operates entirely on source code provided in context.

If the project has an existing OpenAPI spec, merge new endpoints into it rather than generating from scratch.

## Common Framework Patterns

### FastAPI (Python)

FastAPI uses Pydantic models for request and response bodies. The models are directly convertible to JSON Schema. When parsing FastAPI source code:

1. Identify all `APIRouter` instances and their prefix values.
2. Find all route decorators: `@router.get`, `@router.post`, `@router.put`, `@router.patch`, `@router.delete`.
3. Extract the function signature. The return type annotation is the response schema. Parameters annotated with `Query(...)` are query parameters. Parameters annotated with `Path(...)` are path parameters. Parameters typed with a Pydantic `BaseModel` subclass are request bodies.
4. Look for `response_model` in the decorator for the response schema when the return annotation is not a Pydantic model.
5. Look for `status_code` in the decorator for the primary success status code.
6. Look for `responses` in the decorator for additional response codes.

FastAPI generates its own OpenAPI spec at `/openapi.json`. If this is accessible, fetch it and use it as the starting point rather than inferring from source.

### Express.js (Node.js)

Express.js has no built-in type system for route parameters. When parsing Express source code:

1. Identify the Express application or router: `express()`, `express.Router()`.
2. Find all route definitions: `app.get(path, handler)`, `router.post(path, handler)`, etc. Also check `app.use(path, router)` for sub-routers.
3. Extract path parameters from the route path string (`:paramName` syntax).
4. Look for validation middleware (e.g., `express-validator`, `joi`, `zod`) applied before the handler. These define the request schema.
5. Look for TypeScript type annotations if the project uses TypeScript.
6. Look for `res.json(...)` calls in the handler for response body clues.
7. If using `tsoa` or `routing-controllers`, these generate OpenAPI specs — look for their config files and use the generated spec if available.

### Spring Boot (Java/Kotlin)

Spring Boot's Web MVC uses annotation-based routing. When parsing Spring Boot source code:

1. Find all `@RestController` and `@Controller` classes.
2. Extract the `@RequestMapping` prefix from the class level.
3. Find all handler methods annotated with `@GetMapping`, `@PostMapping`, `@PutMapping`, `@PatchMapping`, `@DeleteMapping`.
4. Extract the path from the annotation value, combined with the class-level prefix.
5. Parameters annotated with `@PathVariable` are path parameters. Parameters annotated with `@RequestParam` are query parameters. Parameters annotated with `@RequestBody` are request bodies.
6. The return type of the method is the response schema. Unwrap `ResponseEntity<T>` to get the body type `T`.
7. Look for `springdoc-openapi` or `springfox` configuration — these generate OpenAPI specs and may have customisations applied via annotations (`@Operation`, `@ApiResponse`, `@Schema`).

### Django REST Framework (Python)

DRF uses `ViewSet` and `APIView` classes. When parsing DRF source code:

1. Find the URL configuration (`urls.py`). `DefaultRouter` and `SimpleRouter` register routes automatically from `ViewSet` classes.
2. For `ModelViewSet` subclasses, the following actions are registered by default: `list` (GET /), `create` (POST /), `retrieve` (GET /{id}), `update` (PUT /{id}), `partial_update` (PATCH /{id}), `destroy` (DELETE /{id}).
3. Custom actions decorated with `@action` generate additional routes. The `methods` and `detail` arguments determine the HTTP method and whether the route is resource-level or collection-level.
4. `Serializer` classes define the request and response schemas. Fields in the serializer correspond to schema properties. `read_only=True` fields appear only in responses. `write_only=True` fields appear only in request bodies.
5. Look for `drf-spectacular` or `drf-yasg` — these generate OpenAPI specs.

## Troubleshooting Common Documentation Issues

### Missing request body schema

If the handler accesses `request.body` or `req.body` without a typed schema, document the schema as:

```yaml
schema:
  type: object
  additionalProperties: true
  description: Request body. Schema could not be inferred from source.
```

Note this in the gaps section.

### Inconsistent status codes

If different handlers return different status codes for the same type of result (e.g., some return 200 for creation, some return 201), document the actual behavior for each endpoint and note the inconsistency in the gaps section. Do not normalise to a standard — document what the API actually does.

### Dynamic routes

If the codebase uses dynamic route registration (routes constructed at runtime from configuration), document only the routes that can be statically identified. Note that additional routes may exist.

### Authentication conditional on environment

If authentication is disabled in development mode and enabled in production, document the production behavior. Note the development exception in the server descriptions.

## Output File Naming

When saving the generated OpenAPI YAML to disk, use the following naming convention:

- Single-version API: `openapi.yaml`
- Multi-version API (e.g., v1 and v2 coexist): `openapi-v1.yaml`, `openapi-v2.yaml`
- Draft or work-in-progress: `openapi.draft.yaml`

Always use `.yaml` extension, not `.yml`. Place the file in the project root unless a different location is conventional for the project (e.g., `docs/` or `api/`).

## References

No bundled files.
