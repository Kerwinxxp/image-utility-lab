# Maintainer validation

Validated on Windows with a newly created Python 3.13 CPU environment and the pinned top-level dependencies in `requirements.txt`.

- All seven numerical and workflow tests passed.
- A complete 200-image run produced 2,200 unique view records.
- All four metrics agreed with the prior implementation within 1e-12 absolute difference, including both mechanisms and every epsilon.
- All input images were hash-checked; native shapes and unchanged mask exteriors were checked during measurement.
- The full CSV/JSONL, summary, plotting and submission ZIP workflow completed successfully.
- A fresh clone from GitHub also passed the tests and a three-image measurement/plot/export check in the clean environment.
- The ZIP includes full-precision raw results, input identity, environment information and the actual measurement/plotting source versions.

Real-image reference answers and maintainer-generated curves are intentionally not distributed in this repository. Students should generate and return their own complete results.

Archive hashes are available with the data release. Every archived image was also checked against its manifest hash before upload.
