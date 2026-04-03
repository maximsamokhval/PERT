import nextPlugin from "@next/eslint-plugin-next";
import tseslint from "typescript-eslint";

export default tseslint.config(
  {
    ignores: [
      "node_modules/",
      ".next/",
      "dist/",
      "build/",
      "src/types/api.ts",
    ],
  },
  ...tseslint.configs.recommendedTypeChecked,
  {
    plugins: {
      "@next/next": nextPlugin,
    },
    rules: {
      ...nextPlugin.configs.recommended.rules,
      "@next/next/no-html-link-for-pages": "error",
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
      
      // 1. AST-блокування ручних контрактів API
      "no-restricted-syntax": [
        "error",
        {
          "selector": "TSInterfaceDeclaration[id.name=/.*(Response|Request|DTO|Model|Payload).*/]",
          "message": "Manual API interfaces are PROHIBITED by Constitution. Use auto-generated types from '@/types/api.ts'."
        }
      ],
      
      // 2. Блокування типу 'any'
      "@typescript-eslint/no-explicit-any": "error",

      // 3. Блокування сирого fetch на користь типізованого клієнта
      "no-restricted-globals": [
        "error",
        {
          "name": "fetch",
          "message": "Use typed API client instead of raw fetch to ensure schema alignment."
        }
      ]
    },
    languageOptions: {
      parserOptions: {
        project: "./tsconfig.json",
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
  },
);