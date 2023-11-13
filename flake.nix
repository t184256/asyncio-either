{
  description = "When you have two coroutines to do the same thing, make use of both.";

  inputs.awaitable-property = {
    url = "github:t184256/awaitable-property";
    inputs.nixpkgs.follows = "nixpkgs";
    inputs.flake-utils.follows = "flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }@inputs:
    let
      deps = pyPackages: with pyPackages; [
        # TODO: list python dependencies
      ];
      tools = pkgs: pyPackages: (with pyPackages; [
        pytest pytestCheckHook pytest-asyncio
        coverage pytest-cov
        mypy pytest-mypy
        awaitable-property
      ] ++ [pkgs.ruff]);

      fresh-mypy-overlay = final: prev: {
        pythonPackagesExtensions =
          prev.pythonPackagesExtensions ++ [(pyFinal: pyPrev: {
            mypy =
              if prev.lib.versionAtLeast pyPrev.mypy.version "1.7.0"
              then pyPrev.mypy
              else pyPrev.mypy.overridePythonAttrs (_: {
                version = "1.7.0";
                patches = [];
                src = prev.fetchFromGitHub {
                  owner = "python";
                  repo = "mypy";
                  rev = "refs/tags/v1.7.0";
                  hash = "sha256-2GUEBK3e0GkLFaEg03iSOea2ubvAfcCtVQc06dcqnlE=";
                };
              });
          })];
      };

      asyncio-either-package = {pkgs, python3Packages}:
        python3Packages.buildPythonPackage {
          pname = "asyncio-either";
          version = "0.0.1";
          src = ./.;
          format = "pyproject";
          propagatedBuildInputs = deps python3Packages;
          nativeBuildInputs = [ python3Packages.setuptools ];
          checkInputs = tools pkgs python3Packages;
        };

      asyncio-either-overlay = final: prev: {
        pythonPackagesExtensions =
          prev.pythonPackagesExtensions ++ [(pyFinal: pyPrev: {
            asyncio-either = final.callPackage asyncio-either-package {
              python3Packages = pyFinal;
            };
          })];
      };

      overlay-all = nixpkgs.lib.composeManyExtensions [
        inputs.awaitable-property.overlays.default
        asyncio-either-overlay
        fresh-mypy-overlay
      ];
    in
      flake-utils.lib.eachDefaultSystem (system:
        let
          pkgs = import nixpkgs { inherit system; overlays = [ overlay-all ]; };
          defaultPython3Packages = pkgs.python311Packages;  # force 3.11

          asyncio-either = pkgs.callPackage asyncio-either-package {
            python3Packages = defaultPython3Packages;
          };
        in
        {
          devShells.default = pkgs.mkShell {
            buildInputs = [(defaultPython3Packages.python.withPackages deps)];
            nativeBuildInputs = tools pkgs defaultPython3Packages;
            shellHook = ''
              export PYTHONASYNCIODEBUG=1 PYTHONWARNINGS=error
            '';
          };
          packages.asyncio-either = asyncio-either;
          packages.default = asyncio-either;
        }
    ) // { overlays.default = asyncio-either-overlay; };
}
