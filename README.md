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
  - `debug.js` https://debugjs.net/
  - `sha.js` https://github.com/caligatio/jsSHA

**The `libs/` directory is not part of the WebSys repository.** Its contents are shared, general-purpose dependencies, not WebSys modules. They must be installed separately. The repository includes `public/auth/` and `public/websys/`, along with `private/` containing the initial data files.

Download the latest version of each library from its respective source and place the files in the `public/libs/` directory. Any method of obtaining the files is acceptable.

## Deployment

### Directory layout

```text
server/
|
+- private/
|  |
|  +- websys/ [755]
|     |
|     +- users/ [755]
|     |  |
|     |  +- admin/ [755]
|     |     |
|     |     +- password.txt [666]
|     +- users.tsv [666]
|
+- public/
   |
   +- auth/ [755]
   |  |
   |  +- index.cgi [755]
   |  +- screen.py [644]
   |
   +- libs/ [755]
   |  |
   |  +- *.py [644]
   |  +- *.js [644]
   |
   +- websys/ [755]
      |
      +- admin/ [755]
      |  |
      |  +- api.cgi [755]
      |  +- apiimpl.py [644]
      |  +- index.cgi [755]
      |  +- js.py [644]
      |  +- screen.py [644]
      |  +- style.css [644]
      |  +- sysmgr.js [644]
      |
      +- bin/ [755]
      |  |
      |  +- *.py [644]
      |
      +- api.cgi [755]
      +- apiimpl.py [644]
      +- index.cgi [755]
      +- index_impl.py [644]
      +- websys.js [644]
      +- websys.py [644]
      +- websysconf.py [644]

```
Numbers in brackets indicate file permissions (octal notation). Appropriate permissions may vary depending on the server environment.

- `private/websys/` stores user data, passwords, sessions, and logs outside the web document root.
- `auth/` provides the login and password-change screens.
- `libs/` contains separately supplied shared libraries.
- `websys/` contains the authentication and authorization API, client-side integration code, and configuration.
- `websys/admin/` provides the browser-based administration interface.
- `websys/bin/` contains WebSys's user, group, session, and related management modules.

### Setup

Place the contents of the repository's `public/` directory under the web document root, and keep `private/` alongside it, outside the document root.

1. Copy `public/auth/` and `public/websys/` to the web document root.
2. Install the required shared libraries in `libs/`.
3. Configure the web server to execute `.cgi` files with Python 3, and set their executable permissions as needed.
4. Edit `CSRF_ALLOWED_ORIGIN` in `public/websys/websysconf.py` to match your site's origin. Other settings can generally be left at their defaults.
5. Copy the repository's `private/` directory alongside the web document root, and ensure the CGI process has the necessary permissions to create, modify, and delete files under `private/websys/`.

The default relative paths assume the layout shown above. No database server, package manager, or build process is required for WebSys itself.

### Initial administrator setup

WebSys includes a default administrator account for initial setup:

- Username: `admin`
- Password: The same as the username

After deployment, log in using this account. A password change is required at the first login. Using a strong, unique password is strongly recommended.

Create the necessary user accounts, including an administrator account for ongoing use. Verify that the new administrator account works, then delete the initial `admin` account. Do not continue using the default account for regular administration.

## Configuration

Settings are defined in `public/websys/websysconf.py`. They include:

| Setting | Purpose |
| --- | --- |
| `LIBS_PATH` | Path to the shared Python libraries directory |
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

To manage users, groups, and sessions, access `http(s)://SERVER/websys/admin/`. Administration requires either an account with `is_admin` enabled or the `sysadmin` privilege.

After deployment, the main endpoints are:

| Path | Purpose |
| --- | --- |
| `/auth/` | Login and password-change interface |
| `/websys/admin/` | Administration interface |
| `/websys/api.cgi` | WebSys application API |

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
        websys.send_response('FORBIDDEN', 'text/plain')
        return

    websys.send_response('Hello', 'text/plain')
```

The application's Python import path must include the deployed `websys/` directory. Replace `<privilege-name>` with a permission assigned to the user directly or through a group. Other context methods include `get_user_id()`, `is_member_of()`, and `has_privilege()`.

Browser-side applications can use `websys.js` to request session information and interact with the WebSys API.

## License

WebSys is released under the [MIT License](LICENSE).
