# Web Authentication and Authorization

A lightweight, file-based authentication and authorization system for web applications. It provides user accounts, group-based permissions, session management, and a browser-based administration interface without requiring a database server.

Designed for personal projects and small to medium-sized groups, it emphasizes simple deployment, minimal dependencies, and easy migration between servers.

## Features

- User login, logout, and password changes
- Session management, expiration, and session listing
- User account management, including profile information and account status
- Groups and individual privileges for application-level access control
- Browser-based administration of users, groups, and sessions
- Login attempt limits and account locking
- Activity and system logs
- Text-based storage with no database setup
- Python and JavaScript interfaces for integration with other web applications

## Project structure

```text
websys/
├── auth/
│   ├── index.cgi
│   └── screen.py
├── websys/
│   ├── admin/
│   ├── bin/
│   ├── api.cgi
│   ├── apiimpl.py
│   ├── index.cgi
│   ├── index_impl.py
│   ├── websys.js
│   ├── websys.py
│   └── websysconf.py
└── LICENSE
```

- `auth/` provides the login and password-change screens.
- `websys/` contains the authentication and authorization API, client-side integration code, and configuration.
- `websys/admin/` provides the browser-based administration interface.
- `websys/bin/` contains WebSys's user, group, session, and related management modules.

## Requirements and dependencies

- Python 3
- A web server configured to execute Python CGI scripts (for example, Apache with CGI enabled)
- A writable data directory outside the web document root
- The following **separately supplied libraries**, placed in a sibling `libs/` directory:
  - `util.py`
  - `util.js`
  - `bsb64.py`
  - `sha.js`
  - `debug.js` (used by the administration interface)

**The `libs/` directory is not part of the WebSys repository.** Its contents are shared, general-purpose dependencies, not WebSys modules. They must be installed separately. The repository itself consists of the `auth/` and `websys/` components and their associated files.

## Deployment

Place the repository's `auth/` and `websys/` directories under the web document root, alongside the separately installed libraries. Keep application data in a directory outside the document root.

A typical layout is:

```text
server/
├── public/
│   ├── auth/
│   ├── websys/
│   └── libs/
└── private/
    └── websys/
```

1. Copy `auth/` and `websys/` to the web document root.
2. Install the required shared libraries in `libs/`.
3. Configure the web server to execute `.cgi` files with Python 3, and set their executable permissions as needed.
4. Edit `websys/websysconf.py` for your environment, including the allowed request origin and data storage paths.
5. Ensure the CGI process can write to the private data directory, and provision an initial administrator account before using the management interface.

The default relative paths assume the layout shown above. No database server, package manager, or build process is required for WebSys itself.

## Configuration

Settings are defined in `websys/websysconf.py`. They include:

| Setting | Purpose |
| --- | --- |
| `UTIL_PATH` | Location of the shared Python utility libraries |
| `CSRF_ALLOWED_ORIGIN` | Allowed origin for API requests |
| `DATA_DIR` | Directory used for persistent WebSys data |
| `SESSION_TIMEOUT_SEC` | Session timeout |
| `MAX_SESSIONS_PER_USER` | Maximum sessions per account |
| `LOGIN_FAILURE_MAX` | Number of failed login attempts before locking |
| `LOGIN_LOCK_PERIOD_SEC` | Login lock duration |
| `ANONYMOUS_SESSION_PERIOD_SEC` | Lifetime of anonymous sessions |
| `LOG_FILE_PATH` | System log location |

User, session, and group information is maintained in text-based files under the configured data directory. Backups and migrations can be performed by copying the application files and private data, while preserving their directory layout and permissions.

## Usage

After deployment, the main endpoints are:

| Path | Purpose |
| --- | --- |
| `/auth/` | Login and password-change interface |
| `/websys/admin/` | Administration interface |
| `/websys/api.cgi` | WebSys application API |

The administration interface supports managing user accounts, group privileges, and active sessions. Administration requires the appropriate `sysadmin` permission.

### Using WebSys in a Python CGI application

An application can obtain a request context and check authentication and permissions through `websys.py`:

```python
import websys

def main():
    context = websys.on_access()
    if not context.is_authorized():
        websys.redirect_auth_screen('../')
        return

    if not context.has_permission('privilege'):
        websys.blue_screen('FORBIDDEN')
        return

    websys.send_response('Hello', 'text/plain')
```

The application's Python import path must include the deployed `websys/` directory. The example permission `privilege` must be assigned to the user directly or through a group. Other context methods include `get_user_id()`, `is_member_of()`, and `has_privilege()`.

Browser-side applications can use `websys.js` to request session information and interact with the WebSys API.

## License

WebSys is released under the [MIT License](LICENSE).

Copyright 2020 Takashi Harano.
