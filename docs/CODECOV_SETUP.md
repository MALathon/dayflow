# Setting up Codecov for Dayflow

Codecov provides code coverage reporting for the project. To enable it:

## 1. Sign up for Codecov

1. Go to [codecov.io](https://codecov.io)
2. Sign in with your GitHub account
3. Authorize Codecov to access your repositories

## 2. Add your repository

1. In Codecov, click "Add a repository"
2. Find `MALathon/dayflow` in the list
3. Click to add it

## 3. Get your upload token

1. In your repository settings on Codecov, find the "Upload Token"
2. Copy this token

## 4. Add token to GitHub Secrets

1. Go to your GitHub repository settings
2. Navigate to Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Name: `CODECOV_TOKEN`
5. Value: Paste your upload token
6. Click "Add secret"

## 5. Benefits

Once configured, Codecov will:
- Show code coverage reports on pull requests
- Track coverage trends over time
- Highlight which lines are covered by tests
- Show coverage badges you can add to your README

## Note

The CI is configured to not fail if Codecov upload fails, so the project will work without setting this up. However, having coverage reports is highly recommended for maintaining code quality.
