# Project Development Guidelines

## Branch Strategy

We follow a simple but effective branching strategy:

- **`main`** - The primary branch. Contains production-ready code. Never commit directly to this branch.
- **`feature/`** - Feature branches. Naming format: `feature/<name_of_feature>`

### Branch Lifecycle
1. Create feature branch from `main`
    ```bash
    git checkout main
    git pull
    git checkout -b feature/nameOfFeature
    ```
2. Develop and commit changes
    ```bash
    git add .
    git commit -m "<type_of_commit>: short description"
    ```
3. Push branch to remote
    ```bash
    git push --set-upstream origin feature/ime-funkcionalnosti
    ```
4. Create Pull Request to merge into `main`
5. After review and approval, merge and delete feature branch

---

## Commits

Follow these **Commit Types:** when committing messages

- `feat:` - New feature
- `fix:` - Bug fix
- `doc:` - Documentation updates
- `update:` - General updates, refactoring, or improvements
- `test:` - Adding or modifying tests

## Coding Standards

If possible use the following rule set:
  - functions: snake case (my_func)
  - varibales: camelCase (myVariable)
  - classes: PascalCase (MyClass)


Rules you should definitely follow:
1. If you cannot work with this, use a standard you are already used to, just let it remain the same for the whole project.  
2. Try and use DRY (dont repeat yourself) principle for clean code  
3. Add comments if you think it is necessary (code is too long or too complex)  
4. Make documentation if it seems a good idea (when commenting isnt efficient)

## Pull Request Workflow

## Pull Request Review

## Questions or bugs/issues

- Create an issue, the first one available will review it
- If it's a bigger problem, the whole team should work on it
