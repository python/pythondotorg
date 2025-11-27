'use strict';

function generateReleaseNotesUrl(name) {
    // Match "Python X.Y.Z[aN]"
    const match = name.match(/^Python (\d+)\.(\d+)\.(\d+)((?:a|b|rc)\d*)?$/);
    if (!match) {
        return '';
    }

    const major = match[1];
    const minor = match[2];
    const patch = match[3];
    const prerelease = match[4];  // e.g., "a2", "b1", "rc1" or undefined

    if (prerelease) {
        // Prerelease: https://docs.python.org/3.15/whatsnew/3.15.html
        return `https://docs.python.org/${major}.${minor}/whatsnew/${major}.${minor}.html`;
    } else {
        // Regular release: https://docs.python.org/release/3.13.9/whatsnew/changelog.html
        return `https://docs.python.org/release/${major}.${minor}.${patch}/whatsnew/changelog.html`;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Only run on add page, not edit
    if (!window.location.pathname.endsWith('/add/')) {
        return;
    }

    const nameField = document.getElementById('id_name');
    const releaseNotesUrlField = document.getElementById('id_release_notes_url');

    if (!nameField || !releaseNotesUrlField) {
        return;
    }

    // Track if user has manually edited the field
    let changed = false;
    releaseNotesUrlField.addEventListener('change', function() {
        changed = true;
    });

    nameField.addEventListener('keyup', populate);
    nameField.addEventListener('change', populate);
    nameField.addEventListener('focus', populate);

    function populate() {
        if (changed) {
            return;
        }
        releaseNotesUrlField.value = generateReleaseNotesUrl(nameField.value);
    }
});
