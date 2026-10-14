#!/bin/bash

# Compatibility no-op for callers of the retired per-prompt routing hook.
# Commands and delegate-routing handle explicit requests without guessing a host.
exit 0
