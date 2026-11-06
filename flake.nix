{
  description = "Python development environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          python3
          pkgs.python3Packages.requests
          pkgs.python3Packages.playwright
          pkgs.playwright-driver.browsers
        ];

        # buildInputs = [
        #   pkgs.stdenv.cc.cc.lib
        # ];

        shellHook = ''
          export PLAYWRIGHT_BROWSERS_PATH="${pkgs.playwright-driver.browsers}"
          export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true
        '';

        # export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [
        #   pkgs.stdenv.cc.cc.lib
        # ]}:$LD_LIBRARY_PATH"
        #
        # if [ ! -d .venv ]; then
        #   python -m venv .venv
        # fi
        #
        # source .venv/bin/activate
      };
    };
}
