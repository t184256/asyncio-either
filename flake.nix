{
  description = "When you have two coroutines to do the same thing, make use of both.";

  inputs.awaitable-property = {
    url = "github:t184256/awaitable-property";
    inputs.nixpkgs.follows = "nixpkgs";
    inputs.flake-utils.follows = "flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }@inputs:
    let
      pyDeps = pyPackages: with pyPackages; [
        # TODO: list python dependencies
      ];
      pyTestDeps = pyPackages: with pyPackages; [
        pytest pytestCheckHook pytest-asyncio
        coverage pytest-cov
        awaitable-property
      ];
      pyTools = pyPackages: with pyPackages; [ mypy ];

      tools = pkgs: with pkgs; [
        pre-commit
        ruff
        codespell
        actionlint
        python3Packages.pre-commit-hooks
      ];

      asyncio-either-package = {pkgs, python3Packages}:
        python3Packages.buildPythonPackage {
          pname = "asyncio-either";
          version = "0.0.1";
          src = ./.;
          disabled = python3Packages.pythonOlder "3.11";
          format = "pyproject";
          build-system = [ python3Packages.setuptools ];
          propagatedBuildInputs = pyDeps python3Packages;
          checkInputs = pyTestDeps python3Packages;
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
            buildInputs = [(defaultPython3Packages.python.withPackages (
              pyPkgs: pyDeps pyPkgs ++ pyTestDeps pyPkgs ++ pyTools pyPkgs
            ))];
            nativeBuildInputs = [(pkgs.buildEnv {
              name = "asyncio-either-tools-env";
              pathsToLink = [ "/bin" ];
              paths = tools pkgs;
            })];
            shellHook = ''
              [ -e .git/hooks/pre-commit ] || \
                echo "suggestion: pre-commit install --install-hooks" >&2
              export PYTHONASYNCIODEBUG=1 PYTHONWARNINGS=error
            '';
          };
          packages.asyncio-either = asyncio-either;
          packages.default = asyncio-either;
        }
    ) // { overlays.default = asyncio-either-overlay; };
}
