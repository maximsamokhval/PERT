/** @type {import("openapi-typescript").OpenAPITSOptions} */
const config = {
  input: "http://localhost:8000/openapi.json",
  output: "src/types/api.ts",
  exportType: true,
};

export default config;
