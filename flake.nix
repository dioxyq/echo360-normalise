{
  description = "echo360-normalise nix flake";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };

      pythonEnv = pkgs.python3.withPackages (python: [
        python.requests
        python.playwright
      ]);
      browser = pkgs.playwright-driver.browsers;

      env = ''
          export PLAYWRIGHT_BROWSERS_PATH="${browser}"
          export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true
      '';

      app = pkgs.writeShellApplication {
        name = "echo360-normalise";
        runtimeInputs = [pythonEnv];
        text = env + ''exec python ${./main.py} "$@"'';
      };
    in {
      devShells.${system}.default = pkgs.mkShell {
        packages = [
            pythonEnv
            browser
        ];
        shellHook = env;
      };

      apps.${system}.default = {
        type = "app";
        program = "${app}/bin/echo360-normalise";
      };
    };
}
