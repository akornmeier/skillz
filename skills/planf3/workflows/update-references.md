# Update References

1. **Identify both sides.** Resolve the target plan and every related plan or document. Classify each link as a back reference or forward reference.
2. **Validate and snapshot plans.** Validate every Plan F3 HTML file, then make a temporary pre-edit copy of each one.
3. **Update bidirectionally.** Append the reference to the correct metadata row without duplication and add the reciprocal reference to the related plan when it is also a Plan F3 artifact.
4. **Update history.** Append the current ISO timestamp and one Amendments entry to every plan changed. Preserve all prior metadata.
5. **Validate and repair each plan.** Run the validator with that plan's corresponding `--previous` snapshot. Fix every diagnostic before proceeding, then remove temporary copies.
6. **Report.** List every file touched, reference direction, reciprocal link, and validation result.
