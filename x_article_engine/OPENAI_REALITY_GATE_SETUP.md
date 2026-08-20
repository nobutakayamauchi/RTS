# OpenAI Reality Gate setup

This is the final one-step setup for the X Article Engine tuned-vs-Plain Reality Gate.

## What is already prepared

- Comparison runner: `scripts/run_x_article_openai_compare.py`
- Neutral test fixture: `x_article_engine/fixtures/plain_reality_neutral.json`
- OpenAI live comparator: `x_article_engine/openai_live_compare.py`
- Manual GitHub Actions workflow: `.github/workflows/x-article-engine-openai-reality.yml`
- The runner reads the key only from `OPENAI_API_KEY`.
- The key is not written to the repository or comparison artifact.
- Both outputs are audited and remain `BLOCKED_PENDING_HUMAN`.

## The only secret you need to add

Repository secret name:

```text
OPENAI_API_KEY
```

Use your normal OpenAI API key as the value.

Do not paste the key into source files, fixtures, issue comments, PR comments, or chat.

## GitHub setup steps

1. Open the `nobutakayamauchi/RTS` repository.
2. Open **Settings**.
3. Open **Secrets and variables** → **Actions**.
4. Choose **New repository secret**.
5. Set **Name** to exactly:

   ```text
   OPENAI_API_KEY
   ```

6. Paste your OpenAI API key into **Secret**.
7. Save it.

That completes the key setup.

## After the key is present

The Reality Gate should run with:

- the same OpenAI model for both variants;
- the same neutral brief;
- Tuned v0.9 vs Plain;
- separate audits for each output;
- a comparison artifact for `/human` review.

Default model currently configured by the workflow:

```text
gpt-5.4
```

If that model is unavailable to the API project, select a model that the project can call and use the same model for both variants.

## Local/Oracle alternative

If running from a trusted shell instead of GitHub Actions, set the key only in the process environment and run the comparator:

```bash
export OPENAI_API_KEY='YOUR_KEY_HERE'
python scripts/run_x_article_openai_compare.py --model gpt-5.4
unset OPENAI_API_KEY
```

Avoid putting the key into shell history when possible. GitHub Actions repository secret is the preferred path for this test.

## Expected output

The runner writes:

```text
artifacts/x_article_openai_plain_comparison.json
```

Review Tuned and Plain for:

1. author-specific leakage;
2. loss of useful information or reasoning;
3. unnatural blandness;
4. audit regressions or invented claims.

No merge decision should be made from a successful API call alone. The final decision remains a Human Gate.
