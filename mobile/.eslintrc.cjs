module.exports = {
  root: true,
  env: { browser: true, es2022: true },
  globals: { process: 'readonly' },
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module', ecmaFeatures: { jsx: true } },
  extends: ['eslint:recommended'],
  plugins: ['react'],
  settings: { react: { version: 'detect' } },
  rules: {
    'react/jsx-uses-react': 'error',
    'react/jsx-uses-vars': 'error',
    'react/jsx-no-undef': 'error',
    'react/jsx-key': 'error',
  },
}
