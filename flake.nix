{
  description = "Basic flake for working with manim/janim on python";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    systems.url = "github:nix-systems/default";
    devenv.url = "github:cachix/devenv";
    flake-utils = {
      url = "github:numtide/flake-utils";
      inputs.systems.follows = "systems";
    };
  };

  outputs = { self, nixpkgs, flake-utils, devenv, ... }@inputs:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # Reusable list of GSettings schema dirs
        gsettingsSchemas = builtins.concatStringsSep ":" [
          "${pkgs.gsettings-desktop-schemas}/share/gsettings-schemas/${pkgs.gsettings-desktop-schemas.name}/glib-2.0/schemas"
          "${pkgs.gtk3}/share/gsettings-schemas/${pkgs.gtk3.name}/glib-2.0/schemas"
          "${pkgs.gtk4}/share/gsettings-schemas/${pkgs.gtk4.name}/glib-2.0/schemas"
        ];

        # Libraries needed at runtime
        runtimeLibs = with pkgs; [
          # OpenGL — Mesa must come first so it wins over any stub libGL
          mesa
          mesa.drivers
          libGL
          libGLU
          freeglut

          # X11 (still needed even on Wayland for XWayland fallback)
          xorg.libX11
          xorg.libXext
          xorg.libxcb

          # Qt / Wayland
          glib
          libxkbcommon
          qt6.qtbase
          qt6.qtwayland

          # GTK / GStreamer
          gtk3
          gtk4
          gst_all_1.gstreamer
          gst_all_1.gst-plugins-base

          # Fonts / display
          fontconfig
          freetype
          cairo
          pango

          # System
          dbus
          stdenv.cc.cc.lib
        ];

        devenvRoot = lib:
          let content = builtins.readFile ./devenv.root;
          in lib.mkIf (content != "") content;

      in {
        formatter = pkgs.alejandra;

        packages.devenv-up =
          self.devShells.${system}.default.config.procfileScript;

        devShells.default = devenv.lib.mkShell {
          inherit inputs pkgs;
          modules = [
            ({ pkgs, config, lib, ... }: {
              devenv.root = devenvRoot lib;

              packages = with pkgs;
                [
                  # Dev tools
                  just
                  ruff
                  uv
                  mpv
                  sox
                  typst

                  # Python animation
                  manim

                  # Build deps for manimpango
                  pkg-config
                  cairo
                  pango
                  gobject-introspection
                  gsettings-desktop-schemas
                  gtk3
                  gtk4

                  # Qt Wayland support
                  qt6.qtwayland
                  qt6.qtbase
                ] ++ runtimeLibs;

              env.LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath runtimeLibs;

              # Wayland-native Qt (niri doesn't need XCB forcing)
              env.QT_QPA_PLATFORM = "wayland";
              env.QT_PLUGIN_PATH =
                "${pkgs.qt6.qtbase}/${pkgs.qt6.qtbase.qtPluginPrefix}";

              # Force Mesa to advertise full GL 4.5 — needed for PBO support on AMD
              env.MESA_GL_VERSION_OVERRIDE = "4.5";
              env.MESA_GLSL_VERSION_OVERRIDE = "450";

              # Explicitly use the open-source AMD Vulkan driver
              env.AMD_VULKAN_ICD = "RADV";
              env.VK_ICD_FILENAMES =
                "${pkgs.mesa.drivers}/share/vulkan/icd.d/radeon_icd.x86_64.json";

              # GSettings schemas (required for GTK file chooser dialogs)
              env.GSETTINGS_SCHEMA_DIR = gsettingsSchemas;
            })
          ];
        };
      });
}
