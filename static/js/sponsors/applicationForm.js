$(document).ready(function(){
  const SELECTORS = {
    packageInput:  function() { return $("input[name=package]"); },
    getPackageInfo: function(packageId) { return $("#package_benefits_" + packageId); },
    getPackageBenefits: function(packageId) { return SELECTORS.getPackageInfo(packageId).children(); },
    benefitsInputs: function() { return $("input[id^=id_benefits_]"); },
    getBenefitInput: function(benefitId) { return SELECTORS.benefitsInputs().filter('[value=' + benefitId + ']'); },
    getSelectedBenefits: function() { return SELECTORS.benefitsInputs().filter(":checked"); },
    potentialAddOnInputs:  function() { return $(".potential-add-on input"); },
  }

  SELECTORS.packageInput().change(function(){
    let package = this.value;
    if (package.length == 0) return;

    // clear potential add-on inputs and previous form selection
    SELECTORS.potentialAddOnInputs().prop("checked", false);
    SELECTORS.potentialAddOnInputs().prop("disabled", true);
    $(".selected").removeClass("selected");

    // clear hidden form inputs
    SELECTORS.getSelectedBenefits().each(function(){
      $(this).prop('checked', false);
    });

    // update package benefits display
    $(`.package-${package}-benefit`).addClass("selected");
    $(`.package-${package}-benefit input`).prop("disabled", false);

    // populate hidden inputs according to package's benefits
    SELECTORS.getPackageBenefits(package).each(function(){
      let benefit = $(this).html();
      let benefitInput = SELECTORS.getBenefitInput(benefit);
      benefitInput.prop("checked", true);
    });

    // Mobile version lists a single column to controle the selected
    // benefits and potential add-ons. So, this part of the code
    // controls this logic.
    const mobileVersion = $(".benefit-within-package:hidden").length > 0;
    if (!mobileVersion) return;
    $(".benefit-within-package").hide();  // hide all ticks and potential add-ons inputs
    $(`div[data-package-reference=${package}]`).show()  // display only package's ones
  });
});


// For some unknown reason I couldn't make this logic work with jQuery.
// To don't block the development process, I pulled it off using the classic
// onclick attribute. Refactorings are welcome =]
function potentialAddOnUpdate(benefitId, packageId) {
  const benefitsInputs = Array(...document.querySelectorAll('[data-benefit-id]'));
  const hiddenInput = benefitsInputs.filter((b) => b.getAttribute('data-benefit-id') == benefitId)[0];
  const clickedInput = document.getElementById(`add-on-${ benefitId }-package-${ packageId }`);

  hiddenInput.checked = clickedInput.checked;
};


function updatePackageInput(packageId){
  const packageInput = document.getElementById(`id_package_${ packageId }`);
  packageInput.click();
}
