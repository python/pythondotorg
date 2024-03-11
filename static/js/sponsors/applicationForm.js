const DESKTOP_WIDTH_LIMIT = 1200;

$(document).ready(function(){
  const SELECTORS = {
    packageInput:  function() { return $("input[name=package]"); },
    getPackageInfo: function(packageId) { return $("#package_benefits_" + packageId); },
    getPackageBenefits: function(packageId) { return SELECTORS.getPackageInfo(packageId).children(); },
    benefitsInputs: function() { return $("input[id^=id_benefits_]"); },
    getBenefitInput: function(benefitId) { return SELECTORS.benefitsInputs().filter('[value=' + benefitId + ']'); },
    getSelectedBenefits: function() { return SELECTORS.benefitsInputs().filter(":checked"); },
    tickImages: function() { return $(`.benefit-within-package img`) },
    sectionToggleBtns: function() { return $(".toggle_btn")},
    aLaCarteInputs:  function() { return $("input[name=a_la_carte_benefits]"); },
    standaloneInputs:  function() { return $("input[name=standalone_benefits]"); },
    aLaCarteMessage: function() { return $("#a-la-cart-benefits-disallowed"); },
    standaloneMessage: function() { return $("#standalone-benefits-disallowed"); },
    clearFormButton: function() { return $("#clear_form_btn"); },
    applicationForm: function() { return $("#application_form"); },
  }

  const pkgInputs = $("input[name=package]:checked");
  if (pkgInputs.length > 0 && pkgInputs.val()) {

    // Disable A La Carte inputs based on initial package value
    if (pkgInputs.attr("allow_a_la_carte") !== "true"){
      let msg = "Cannot add a la carte benefit with the selected package.";
      SELECTORS.aLaCarteInputs().attr("title", msg);
      SELECTORS.aLaCarteMessage().removeClass("hidden");
      SELECTORS.aLaCarteInputs().prop("checked", false);
      SELECTORS.aLaCarteInputs().prop("disabled", true);

    }

    // Disable Standalone benefits inputs
    let msg ="Cannot apply for standalone benefit with the selected package.";
    SELECTORS.standaloneInputs().prop("checked", false);
    SELECTORS.standaloneInputs().prop("disabled", true);
    SELECTORS.standaloneMessage().removeClass("hidden");
    SELECTORS.standaloneInputs().attr("title", msg);

    // Update mobile selection
    mobileUpdate(pkgInputs.val());
  } else {
    // disable a la carte if no package selected at the first step
    SELECTORS.aLaCarteInputs().prop("disabled", true);
  }

  SELECTORS.sectionToggleBtns().click(function(){
    const section = $(this).data('section');
    const className = ".section-" + section + "-content";
    $(className).toggle();
  });

  SELECTORS.clearFormButton().click(function(){
    SELECTORS.aLaCarteInputs().prop('checked', false).prop('selected', false);
    SELECTORS.benefitsInputs().prop('checked', false).prop('selected', false);
    SELECTORS.packageInput().prop('checked', false).prop('selected', false);
    SELECTORS.standaloneInputs()
      .prop('checked', false).prop('selected', false).prop("disabled", false);

    SELECTORS.tickImages().each((i, img) => {
      const initImg = img.getAttribute('data-initial-state');
      const src = img.getAttribute('src');

      if (src !== initImg) {
        img.setAttribute('data-next-state', src);
      }

      img.setAttribute('src', initImg);
    });
    $(".selected").removeClass("selected");
    $('.custom-fee').hide();
  });

  SELECTORS.packageInput().click(function(){
    let package = this.value;
    if (package.length == 0) {
      SELECTORS.standaloneInputs().prop("disabled", false);
      SELECTORS.standaloneMessage().addClass("hidden");
      return;
    }

    // clear previous customizations
    SELECTORS.tickImages().each((i, img) => {
      const initImg = img.getAttribute('data-initial-state');
      const src = img.getAttribute('src');

      if (src !== initImg) {
        img.setAttribute('data-next-state', src);
      }

      img.setAttribute('src', initImg);
    });
    $(".selected").removeClass("selected");

    // clear hidden form inputs
    SELECTORS.getSelectedBenefits().each(function(){
      $(this).prop('checked', false);
    });

    // update package benefits display
    $(`#pkg_container_${package}`).addClass("selected");
    $(`.package-${package}-benefit`).addClass("selected");
    $(`.package-${package}-benefit input`).prop("disabled", false);

    let msg ="Cannot apply for standalone benefit with the selected package.";
    SELECTORS.standaloneInputs().prop("checked", false);
    SELECTORS.standaloneInputs().prop("disabled", true);
    SELECTORS.standaloneMessage().removeClass("hidden");
    SELECTORS.standaloneInputs().attr("title", msg);

    // Disable a la carte benefits if package disables it
    if ($(this).attr("allow_a_la_carte") !== "true") {
      msg ="Cannot add a la carte benefit with the selected package.";
      SELECTORS.aLaCarteInputs().attr("title", msg);
      SELECTORS.aLaCarteMessage().removeClass("hidden");
      SELECTORS.aLaCarteInputs().prop("checked", false);
      SELECTORS.aLaCarteInputs().prop("disabled", true);
    } else {
      SELECTORS.aLaCarteInputs().attr("title", "");
      SELECTORS.aLaCarteMessage().addClass("hidden");
      SELECTORS.aLaCarteInputs().not('.soldout').prop("disabled", false);
    }

    // populate hidden inputs according to package's benefits
    SELECTORS.getPackageBenefits(package).each(function(){
      let benefit = $(this).html();
      let benefitInput = SELECTORS.getBenefitInput(benefit);
      benefitInput.prop("checked", true);
    });

    // hide previous custom fee messages
    $('.custom-fee').hide();

    mobileUpdate(package);
  });
});


function mobileUpdate(packageId) {
  const width = window.innerWidth
    || document.documentElement.clientWidth
    || document.body.clientWidth;
  const mobileVersion = width <= DESKTOP_WIDTH_LIMIT;
  if (!mobileVersion) return;
  $(".benefit-within-package").hide();  // hide all ticks and potential a la carte inputs
  $(`div[data-package-reference=${packageId}]`).show()  // display only package's ones
}


// For an unknown reason I couldn't make this logic work with jQuery.
// To don't block the development process, I pulled it off using the classic
// onclick attribute. Refactorings are welcome =]
function benefitUpdate(benefitId, packageId) {
  // Change tick image for the benefit. Can't directly change the url for the image
  // due to our current static files storage.
  const clickedImg = document.getElementById(`benefit-${ benefitId }-package-${ packageId }`);

  // Img container must have "selected" to class to be editable
  if (!clickedImg.parentElement.classList.contains('selected')) return;

  const newSrc = clickedImg.getAttribute("data-next-state");
  clickedImg.setAttribute("data-next-state", clickedImg.src);

  // Update benefit's hidden input (can't rely on click event though)
  const benefitsInputs = Array(...document.querySelectorAll('[data-benefit-id]'));
  const hiddenInput = benefitsInputs.filter((b) => b.getAttribute('data-benefit-id') == benefitId)[0];
  hiddenInput.checked = !hiddenInput.checked;
  clickedImg.src = newSrc;

  // Check if there are any type of customization. If so, display custom-fee label.
  let pkgBenefits = Array(...document.getElementById(`package_benefits_${packageId}`).children).map(div => div.textContent).sort();
  let checkedBenefis = Array(...document.querySelectorAll('[data-benefit-id]')).filter(e => e.checked).map(input => input.value).sort();

  const hasAllBenefts = pkgBenefits.reduce((sum, id) => sum && checkedBenefis.includes(id), true);
  const sameBenefitsNum = pkgBenefits.length === checkedBenefis.length;

  const customFeeElems = Array(...document.getElementsByClassName(`custom-fee-${packageId}`));
  if (hasAllBenefts && sameBenefitsNum) {
    customFeeElems.map(e => e.style.display = 'none');
  } else {
    customFeeElems.map(e => e.style.display = 'initial');
  }
};

// Callback function when user selects a package;
function updatePackageInput(packageId){
  const packageInput = document.getElementById(`id_package_${ packageId }`);

  // no need to update if package is already selected
  const container = packageInput.parentElement;
  if (container.classList.contains("selected")) return;

  packageInput.click();
}
