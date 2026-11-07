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

## Requirements and dependencies

- Python 3
- A web server configured to execute Python CGI scripts (for example, Apache with CGI enabled)
- A writable data directory outside the web document root
- The following **separately supplied libraries**, placed in a sibling `libs/` directory:
  - `util.py` https://libutil.com/
  - `util.js` https://libutil.com/
  - `bsb64.py` https://libutil.com/bsb64/
  - `sha.js` https://github.com/caligatio/jsSHA
  - `debug.js` https://debugjs.net/

**The `libs/` directory is not part of the WebSys repository.** Its contents are shared, general-purpose dependencies, not WebSys modules. They must be installed separately. The repository includes the `auth/` and `websys/` components, along with `_private/` containing the initial data files.

## Deployment

### Directory layout

```text
server/
|
+- private/
|  |
|  +- websys/
|     |
|     +- users/
|     |  |
|     |  +- admin/
|     |     |
|     |     +- password.txt
|     +- users.tsv
|
+- public/
   |
   +- auth/
   |  |
   |  +- index.cgi
   |  +- screen.py
   |
   +- libs/
   +- websys/
      |
      +- admin/
      +- bin/
      +- api.cgi
      +- apiimpl.py
      +- index.cgi
      +- index_impl.py
      +- websys.js
      +- websys.py
      +- websysconf.py

```
- `private/websys/` stores user data, passwords, sessions, and logs outside the web document root.
- `auth/` provides the login and password-change screens.
- `libs/` contains separately supplied shared libraries.
- `websys/` contains the authentication and authorization API, client-side integration code, and configuration.
- `websys/admin/` provides the browser-based administration interface.
- `websys/bin/` contains WebSys's user, group, session, and related management modules.

### Setup

Place the repository's `auth/` and `websys/` directories under the web document root, alongside the separately installed libraries. Keep application data in a directory outside the document root.

1. Copy `auth/` and `websys/` to the web document root.
2. Install the required shared libraries in `libs/`.
3. Configure the web server to execute `.cgi` files with Python 3, and set their executable permissions as needed.
4. Edit `websys/websysconf.py` for your environment, including the allowed request origin and data storage paths.
5. Copy the contents of `_private/websys/` to `private/websys/` outside the web document root, and ensure the CGI process can write to this directory.

The default relative paths assume the layout shown above. No database server, package manager, or build process is required for WebSys itself.

### Initial administrator setup

WebSys includes a default administrator account for initial setup:

- Username: `admin`
- Password: The same as the username

After deployment, log in using this account. A password change is required at the first login. Using a strong, unique password is strongly recommended.

Create the necessary user accounts, including an administrator account for ongoing use. Verify that the new administrator account works, then delete the initial `admin` account. Do not continue using the default account for regular administration.

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

    if not context.has_permission('<privilege-name>'):
        websys.blue_screen('FORBIDDEN')
        return

    websys.send_response('Hello', 'text/plain')
```

The application's Python import path must include the deployed `websys/` directory. Replace `<privilege-name>` with a permission assigned to the user directly or through a group. Other context methods include `get_user_id()`, `is_member_of()`, and `has_privilege()`.

Browser-side applications can use `websys.js` to request session information and interact with the WebSys API.

## License

WebSys is released under the [MIT License](LICENSE).
