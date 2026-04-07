{
  description = "Dev shell for JAnim + PySide6 on Wayland";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        # Packages that need to be included in the runtime path
        runtimeLibs = with pkgs; [
          python313

          # OpenGL
          mesa
          libGL
          libGLU
          glib
          fontconfig

          # Keymap handling
          libxkbcommon

          # X11 (still needed even on Wayland for XWayland fallback)
          libx11
          libxext
          libxcb

          # Wayland
          wayland
          wayland-protocols

          # Audio
          alsa-lib

          # Fonts / display
          freetype

          # System
          dbus
          stdenv.cc.cc.lib
        ];
      in {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [ uv ] ++ runtimeLibs;

          env.QT_QPA_PLATFORM = "wayland";
          env.QT_API = "pyside6";
          env.QT_WAYLAND_DISABLE_WINDOWDECORATION = "1";
          env.LIBGL_ALWAYS_SOFTWARE = "0";

          env.LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath runtimeLibs;
          # Sync dependencies
          shellHook = ''
            uv sync --frozen
            export VIRTUAL_ENV=$PWD/.venv
            export LD_LIBRARY_PATH="$VIRTUAL_ENV/lib/python3.13/site-packages/PySide6:$LD_LIBRARY_PATH"
            echo "TESTING COMPILATION"
            uv run main.py
          '';
        };
      });
}
