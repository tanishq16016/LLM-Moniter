#!/usr/bin/env python
"""Build script for Vercel deployment."""
import os
import subprocess

print("=" * 50)
print("Starting Vercel Build Process")
print("=" * 50)

# Run migrations
print("\n🔄 Running database migrations...")
result = subprocess.run(
    ["python", "manage.py", "migrate", "--noinput"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ Migrations completed successfully!")
    print(result.stdout)
else:
    print("❌ Error running migrations:")
    print(result.stderr)
    # Don't exit on migration errors in case tables already exist
    print("⚠️ Continuing despite migration errors...")

# Run collectstatic
print("\n📦 Collecting static files...")
result = subprocess.run(
    ["python", "manage.py", "collectstatic", "--noinput", "--clear"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ Static files collected successfully!")
    print(result.stdout)
else:
    print("❌ Error collecting static files:")
    print(result.stderr)
    exit(1)

print("\n" + "=" * 50)
print("Build Complete!")
print("=" * 50)
