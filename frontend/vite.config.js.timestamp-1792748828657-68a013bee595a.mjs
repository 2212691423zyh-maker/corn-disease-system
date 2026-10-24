// vite.config.js
import { defineConfig } from "file:///D:/bs/frontend/node_modules/vite/dist/node/index.js";
import vue from "file:///D:/bs/frontend/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import AutoImport from "file:///D:/bs/frontend/node_modules/unplugin-auto-import/dist/vite.js";
import Components from "file:///D:/bs/frontend/node_modules/unplugin-vue-components/dist/vite.js";
import { ElementPlusResolver } from "file:///D:/bs/frontend/node_modules/unplugin-vue-components/dist/resolvers.js";
import { resolve } from "path";
var __vite_injected_original_dirname = "D:\\bs\\frontend";
var vite_config_default = defineConfig({
  plugins: [
    vue(),
    AutoImport({ resolvers: [ElementPlusResolver()] }),
    Components({ resolvers: [ElementPlusResolver()] })
  ],
  resolve: {
    alias: { "@": resolve(__vite_injected_original_dirname, "src") }
  },
  server: {
    port: 5173,
    host: "0.0.0.0",
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/uploads": { target: "http://localhost:8000", changeOrigin: true }
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuanMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJEOlxcXFxic1xcXFxmcm9udGVuZFwiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9maWxlbmFtZSA9IFwiRDpcXFxcYnNcXFxcZnJvbnRlbmRcXFxcdml0ZS5jb25maWcuanNcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfaW1wb3J0X21ldGFfdXJsID0gXCJmaWxlOi8vL0Q6L2JzL2Zyb250ZW5kL3ZpdGUuY29uZmlnLmpzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZSdcbmltcG9ydCB2dWUgZnJvbSAnQHZpdGVqcy9wbHVnaW4tdnVlJ1xuaW1wb3J0IEF1dG9JbXBvcnQgZnJvbSAndW5wbHVnaW4tYXV0by1pbXBvcnQvdml0ZSdcbmltcG9ydCBDb21wb25lbnRzIGZyb20gJ3VucGx1Z2luLXZ1ZS1jb21wb25lbnRzL3ZpdGUnXG5pbXBvcnQgeyBFbGVtZW50UGx1c1Jlc29sdmVyIH0gZnJvbSAndW5wbHVnaW4tdnVlLWNvbXBvbmVudHMvcmVzb2x2ZXJzJ1xuaW1wb3J0IHsgcmVzb2x2ZSB9IGZyb20gJ3BhdGgnXG5cbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZyh7XG4gIHBsdWdpbnM6IFtcbiAgICB2dWUoKSxcbiAgICBBdXRvSW1wb3J0KHsgcmVzb2x2ZXJzOiBbRWxlbWVudFBsdXNSZXNvbHZlcigpXSB9KSxcbiAgICBDb21wb25lbnRzKHsgcmVzb2x2ZXJzOiBbRWxlbWVudFBsdXNSZXNvbHZlcigpXSB9KSxcbiAgXSxcbiAgcmVzb2x2ZToge1xuICAgIGFsaWFzOiB7ICdAJzogcmVzb2x2ZShfX2Rpcm5hbWUsICdzcmMnKSB9LFxuICB9LFxuICBzZXJ2ZXI6IHtcbiAgICBwb3J0OiA1MTczLFxuICAgIGhvc3Q6ICcwLjAuMC4wJyxcbiAgICBwcm94eToge1xuICAgICAgJy9hcGknOiB7IHRhcmdldDogJ2h0dHA6Ly9sb2NhbGhvc3Q6ODAwMCcsIGNoYW5nZU9yaWdpbjogdHJ1ZSB9LFxuICAgICAgJy91cGxvYWRzJzogeyB0YXJnZXQ6ICdodHRwOi8vbG9jYWxob3N0OjgwMDAnLCBjaGFuZ2VPcmlnaW46IHRydWUgfSxcbiAgICB9LFxuICB9LFxufSlcbiJdLAogICJtYXBwaW5ncyI6ICI7QUFBa08sU0FBUyxvQkFBb0I7QUFDL1AsT0FBTyxTQUFTO0FBQ2hCLE9BQU8sZ0JBQWdCO0FBQ3ZCLE9BQU8sZ0JBQWdCO0FBQ3ZCLFNBQVMsMkJBQTJCO0FBQ3BDLFNBQVMsZUFBZTtBQUx4QixJQUFNLG1DQUFtQztBQU96QyxJQUFPLHNCQUFRLGFBQWE7QUFBQSxFQUMxQixTQUFTO0FBQUEsSUFDUCxJQUFJO0FBQUEsSUFDSixXQUFXLEVBQUUsV0FBVyxDQUFDLG9CQUFvQixDQUFDLEVBQUUsQ0FBQztBQUFBLElBQ2pELFdBQVcsRUFBRSxXQUFXLENBQUMsb0JBQW9CLENBQUMsRUFBRSxDQUFDO0FBQUEsRUFDbkQ7QUFBQSxFQUNBLFNBQVM7QUFBQSxJQUNQLE9BQU8sRUFBRSxLQUFLLFFBQVEsa0NBQVcsS0FBSyxFQUFFO0FBQUEsRUFDMUM7QUFBQSxFQUNBLFFBQVE7QUFBQSxJQUNOLE1BQU07QUFBQSxJQUNOLE1BQU07QUFBQSxJQUNOLE9BQU87QUFBQSxNQUNMLFFBQVEsRUFBRSxRQUFRLHlCQUF5QixjQUFjLEtBQUs7QUFBQSxNQUM5RCxZQUFZLEVBQUUsUUFBUSx5QkFBeUIsY0FBYyxLQUFLO0FBQUEsSUFDcEU7QUFBQSxFQUNGO0FBQ0YsQ0FBQzsiLAogICJuYW1lcyI6IFtdCn0K
