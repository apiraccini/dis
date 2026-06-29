# Frontend

React SPA for document management, consuming the REST API under `/api/*`. Minimal but functional; standard dark theme.

## Document list

- **Requirement: Document list view** — The UI SHALL display all documents in a table showing filename, tags, status, size, chunk count, and upload date.
  - Scenario: rows render — GIVEN the API returns documents, WHEN the view loads, THEN one row per document is shown with its metadata.
  - Scenario: empty state — GIVEN the API returns zero documents, WHEN the view loads, THEN an empty-state message is shown instead of a table.
  - Scenario: loading state — GIVEN the list request is in flight, WHEN the view loads, THEN a loading indicator is shown.
  - Scenario: error state — GIVEN the list request fails, WHEN the view loads, THEN an error message with a retry affordance is shown.

- **Requirement: Status badge** — Each document row SHALL show a status badge for `processing`, `ready`, or `failed`.
  - Scenario: failed surfaces error — GIVEN a document with status `failed` and an `error_message`, WHEN its row renders, THEN the badge indicates failure and the `error_message` is available on hover.

- **Requirement: Poll while processing** — The UI SHALL re-fetch the document list on an interval while any document has status `processing`, and SHALL stop polling when none do.
  - Scenario: transition to ready — GIVEN a `processing` document, WHEN a later poll returns it as `ready`, THEN the row updates and polling stops once no row is `processing`.

## Upload

- **Requirement: Upload with tags** — The UI SHALL provide an upload action (modal) accepting one file and zero or more tags, submitting them to the upload endpoint as multipart form data with comma-separated tags.
  - Scenario: tag chips — GIVEN the tag input, WHEN the user types a tag and confirms, THEN it becomes a removable chip; all chips are submitted comma-separated.
  - Scenario: success refetches — GIVEN a valid file, WHEN upload returns 200 or 202, THEN the modal closes and the list refetches.
  - Scenario: parse error inline — GIVEN a file the backend rejects with 422, WHEN upload fails, THEN the error message is shown inside the modal and the modal stays open.

## Delete

- **Requirement: Delete document** — Each document row SHALL provide a delete action that requires confirmation before deleting, then refetches the list.
  - Scenario: confirm delete — GIVEN a document row, WHEN the user triggers delete and confirms, THEN the document is deleted and the list refetches.
  - Scenario: cancel delete — GIVEN a delete confirmation, WHEN the user cancels, THEN no request is made.
