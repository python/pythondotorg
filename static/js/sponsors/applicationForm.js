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


  const initialPackage = $("input[name=package]:checked").val();
  if (initialPackage && initialPackage.length > 0) mobileUpdate(initialPackage);

  SELECTORS.packageInput().click(function(){
    let package = this.value;
    console.log(package);
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

    mobileUpdate(package);
  });
});


function mobileUpdate(packageId) {
  // Mobile version lists a single column to controle the selected
  // benefits and potential add-ons. So, this part of the code
  // controls this logic.
  console.log(packageId);
  console.log(`div[data-package-reference=${packageId}]`);
  const mobileVersion = $(".benefit-within-package:hidden").length > 0;
  if (!mobileVersion) return;
  $(".benefit-within-package").hide();  // hide all ticks and potential add-ons inputs
  $(`div[data-package-reference=${packageId}]`).show()  // display only package's ones
}


// For an unknown reason I couldn't make this logic work with jQuery.
// To don't block the development process, I pulled it off using the classic
// onclick attribute. Refactorings are welcome =]
function potentialAddOnUpdate(benefitId, packageId) {
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
};


function updatePackageInput(packageId){
  const packageInput = document.getElementById(`id_package_${ packageId }`);
  packageInput.click();
}
