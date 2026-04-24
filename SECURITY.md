# Security Policy

## Supported Versions

We release security patches for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |
| < latest| :x:                |

We recommend always running the latest version. Updates are published to the `master` branch and tagged as releases.

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**Please do not open a public GitHub issue for security vulnerabilities.**

Instead, report security issues privately:

- **Email**: security@openglaze.com
- **Subject**: `[SECURITY] Brief description of the issue`
- **Include**:
  - Affected component(s) and version
  - Step-by-step reproduction instructions
  - Impact assessment (what could an attacker do?)
  - Suggested fix (if you have one)

### Response Process

1. **Acknowledgment** — We will acknowledge receipt within 48 hours
2. **Investigation** — We will investigate and validate the issue
3. **Fix & Test** — We will develop and test a fix
4. **Disclosure** — We will coordinate disclosure with you
5. **Release** — We will release a patched version and publish a security advisory

### Disclosure Timeline

We follow responsible disclosure:

- We ask reporters to allow **90 days** before public disclosure
- We will work to release a fix as quickly as possible
- We will credit you in the security advisory (with your permission)

## Security Best Practices for Self-Hosting

If you are self-hosting OpenGlaze, follow these practices:

### Authentication

- Use strong, unique passwords for all admin accounts
- Enable multi-factor authentication (MFA) where supported
- Rotate API keys and secrets regularly

### Database

- Use PostgreSQL in production (not SQLite)
- Enable SSL/TLS for database connections
- Restrict database access to the application server only
- Set up automated backups

### Network

- Run OpenGlaze behind a reverse proxy (nginx, Caddy, Traefik)
- Enable HTTPS with valid TLS certificates (Let's Encrypt)
- Configure appropriate firewall rules
- Use a CDN for static assets (optional)

### Environment

- Keep `.env` files secure and never commit them to version control
- Use strong secrets for `SECRET_KEY`, `KRATOS_HOOK_KEY`, etc.
- Regularly update dependencies: `pip install --upgrade -r requirements.txt`
- Monitor for security advisories in dependencies

### Docker

- Run containers as non-root users
- Keep base images updated
- Scan images for vulnerabilities: `docker scan openglaze`
- Use read-only filesystems where possible

### Monitoring

- Enable logging and monitor for suspicious activity
- Set up alerts for failed login attempts
- Review access logs regularly
- Consider using a Web Application Firewall (WAF)

## Known Security Considerations

### Current Architecture

- OpenGlaze is designed to be a single-tenant application per instance
- Multi-tenancy (if needed) should be implemented at the infrastructure level
- File uploads are validated but should be further restricted in production
- AI features may process sensitive glaze formulations — ensure data stays within your control

### Dependency Security

We monitor dependencies for known vulnerabilities:

```bash
# Check Python dependencies
pip install safety
safety check

# Check Docker images
docker scan openglaze:latest
```

## Security-Related Configuration

Key security settings in your `.env`:

```bash
# Required: Strong random secret
SECRET_KEY=your-256-bit-random-secret-here

# Required for production
FLASK_ENV=production

# Recommended: Enable HTTPS only
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax

# Rate limiting (requests per minute)
RATE_LIMIT_PER_MINUTE=60
```

## Hall of Fame

We thank the following security researchers who have responsibly disclosed vulnerabilities:

*None yet — be the first!*

## Contact

- **Security Team**: security@openglaze.com
- **GPG Key**: [Download public key](https://openglaze.com/security.gpg)
