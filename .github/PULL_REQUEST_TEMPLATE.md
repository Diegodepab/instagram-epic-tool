## Summary

<!-- Explain what changes and why. Do not include real Instagram exports or personal data. -->

## Change Type

- [ ] `fix` — bug fix
- [ ] `feat` — new feature
- [ ] `perf` — performance improvement
- [ ] `refactor` — internal change
- [ ] `docs` — documentation
- [ ] `test` — tests
- [ ] `build` / `ci` — tooling or pipeline
- [ ] Breaking change

## Verification

- [ ] Backend tests pass: `PYTHONPATH=src python -m unittest discover -s tests -v`
- [ ] Frontend lint passes: `npm run lint`
- [ ] Frontend production build passes: `npm run build`
- [ ] Docker configuration is valid: `docker compose config --quiet`
- [ ] User, security, deployment, or architecture docs were updated when needed
- [ ] No ZIP exports, generated datasets, credentials, or personal usernames were committed

## Deployment

- [ ] Tested locally
- [ ] Ready to validate in the private `Apolo_Dev` environment before production
