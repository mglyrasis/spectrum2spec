spectrum2spec
========

spectrum2spec is a tool to generate a YAML file with the SPECTRUM museum collection standard.

Ref: https://collectionstrust.org.uk/spectrum/

The resulting spec file standardizes formatting to a large degree, except in cases where the intent was unclear,
e.g., the examples for Object information groups -> Object identification information -> Other number.

When running the script for the first time, the pages will be cached in an SQLite database. This .sqlite file can be
safely removed to force a refresh of the data.

The output filename will be `spectrum-<today's date>.yaml` in the current directory.

See `spectrum.example.yaml` for an example of the complete output of the script.

## Usage

```bash
poetry install
poetry run python general_yaml_spec.py
``` 

## Resultant schema structure

```yaml
information_group_type:
  description:
  name:
  url:
  members:
    information_group:
      description:
      name:
      url:
      members:
        unit_of_information:
          name:
          url:
          definition:
          how_to_record:
          examples:
          use:
          information_group:
          members [Optional, occurring when there are sub-units of information]:
            unit_of_information:
              name:
              url:
              definition:
              how_to_record:
              examples:
              use:
              information_group:
```

## Example displaying a single unit of information (field)
```yaml
record_management_information_groups:
  description: The units of information in these groups are used to annotate the records
    in your documentation system.
  name: Record management information groups
  url: /spectrum/information-requirements/record-management-information-groups/
  members:
    amendment_history:
      name: Amendment history
      url: /resource/amendment-history/
      members:
        amendment_history_authoriser:
          definition: The Person giving final approval for a piece of information
            being added to a record.
          examples:
          - See under Person.
          how_to_record: It will be necessary to use several units of information,
            including, for example, a surname and a forename. The descriptions for
            these information units are gathered together under the Person heading.
            The organisation may have standard forms of names for use.
          information_group: Amendment history
          name: Amendment history authoriser
          url: /resource/amendment-history-authoriser
          use: Use with Recorder as required for each amendment to a record where
            a specific unit identifying the authoriser (eg Auditor, Valuer) is not
            available. This unit should be associated with the unit of information
            being amended.
```
