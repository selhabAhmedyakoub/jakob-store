
// Replace with your own secret key
document.addEventListener("DOMContentLoaded", async function() {

const stripe = Stripe('pk_test_51OsPm5H4R8xQsOnyVMlrYFV9m2W9NUEIc1UxBYxvZ9qkTukGAB8CYa0sYvB7GJmWrlMNQOnWuTAfJa6NeRJKyAjb00Ajap6NiO');

const appearance = { /* appearance */ };
const options = { mode: 'billing' };
const elements = stripe.elements({ clientSecret });
const addressElement = elements.create('address', options);
const paymentElement = elements.create('payment');
addressElement.mount('#address-element');
paymentElement.mount('#payment-element');

const session = await stripe.checkout.sessions.create({
  payment_method_types: ['card'],
  line_items: [
    // Add your line items here
  ],
  mode: 'payment',
  success_url: 'http://127.0.0.1:5000/success',
  cancel_url: 'http://127.0.0.1:5000/cancel',
  billing_address_collection: 'required',
  shipping_address_collection: {
    allowed_countries: ['US', 'CA'],
  },
});
console.log(session);
});
document.addEventListener("DOMContentLoaded", async function() {

  const countryStateInfo = {
    USA: {
      "Los Angeles": ["90001", "90002", "90003", "90004"],
      "San Diego": ["92093", "92101"],
      Dallas: ["75201", "75202"],
      Austin: ["73301", "73344"],
    },
    Algeria: {
      "Adrar": ["01000", "01001", "01002", "01101"],
      "Chlef": ["02000", "02001"],
      Laghouat: ["03000", "03003"],
      "Oum ElBouaghi" : ["04011", "04122"],
      "Batna" : ["05522", "05121", "05128"],
      "Béjaïa" : ["06722", "06221"],
    },
    Germany: {
      Munich: ["80331", "80333", "80335", "80336"],
      Nuremberg: ["90402", "90403", "90404", "90405"],
      Frankfurt: ["60306", "60308", "60309", "60310"],
      Surat: ["55246", "55247", "55248", "55249"], 
    },
  };
  window.onload = function () {
    const countrySelection = document.querySelector("#Country");
    const citySelection = document.querySelector("#City");
    const zipSelection = document.querySelector("#Zip");
  
    citySelection.disabled = true;
    zipSelection.disabled = true;
  
    // Clear all options 
    countrySelection.length = 1;
    citySelection.length = 1;
    zipSelection.length = 1;
  
    for (let country in countryStateInfo) {
      countrySelection.options[countrySelection.options.length] = new Option(
        country,
        country
      );
    }
  
    countrySelection.onchange = (e) => {
      citySelection.disabled = false;
      citySelection.length = 1;
      zipSelection.length = 1;
  
      let selectedCountry = countrySelection.value;
      for (let city in countryStateInfo[selectedCountry]) {
        citySelection.options[citySelection.options.length] = new Option(city, city);
      }
      citySelection.onchange(); 
    };
  
    citySelection.onchange = (e) => {
      zipSelection.disabled = false;
      zipSelection.length = 1;
  
      let selectedCountry = countrySelection.value;
      let selectedCity = citySelection.value;
  
      console.log("Selected Country:", selectedCountry); 
      console.log("Selected City:", selectedCity); 
  
      let zips = countryStateInfo[selectedCountry][selectedCity];
      for (let zip of zips) {
        zipSelection.options[zipSelection.options.length] = new Option(zip, zip);
      }
    };
  };
});
var script = document.createElement('script');
script.src = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js";
script.integrity = "sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL";
script.crossOrigin = "anonymous";
document.head.appendChild(script);

document.addEventListener("DOMContentLoaded", function() {

  const mainImage = document.querySelector(".mainImage");
  const smallImages = document.querySelectorAll(".miniImage");
  smallImages.forEach(function(smallImage) {
    smallImage.addEventListener("click", function() {
      mainImage.src = smallImage.src;
      mainImage.style.width = "100%";
      mainImage.style.height = "auto";
    });
  });
});



document.addEventListener("DOMContentLoaded", function() {  1
  

   // Get the <h1> element which contain the product name  
  const productNameElement = document.querySelector('.product_name1');

   // Get the product name input field
  const productNameInput = document.getElementById('product-name-input');

   // Set the initial value of the input field to the text of the <h1> element
  productNameInput.value = productNameElement.textContent;

   // Update the input field whenever the text in the <h1> element changes
  productNameElement.addEventListener('input', function() {
    productNameInput.value = productNameElement.textContent;
  });


  // Get the <h5> element which contain the product price
  const productpriceElement = document.querySelector('.product_price1');
// Get the product price input field
  const productpriceInput = document.getElementById('product-price-input');

   // Set the initial value of the input field to the text of the <h5> element
  productpriceInput.value = productpriceElement.textContent;

  // Update the input field whenever the text in the <h5> element changes
  productpriceElement.addEventListener('input', function() {
    productpriceInput.value = productpriceElement.textContent;
  });





});
//the javascript code which ket the user increment or decrement the order quantity 
document.addEventListener('DOMContentLoaded', function() {
  var quantity = 1;
  var minusButton = document.getElementById("minus-button");

  document.getElementById("selectedquantity").value = quantity.toString();

  function incrementQuantity() {
    quantity++;
    updateQuantity();
  }

  function decrementQuantity() {
    if (quantity > 1) {
      quantity--;
      updateQuantity();
    }
  }

  function updateQuantity() {
    var quantityInput = document.getElementById("selectedquantity");
    quantityInput.value = quantity.toString();
    
// Enable or disable the minus button based on the quantity value
    if (quantity > 1) {
      minusButton.disabled = false;
    } else {
      minusButton.disabled = true; 
    }
  }

// Add event listeners to the increment and decrement buttons
  document.getElementById("plus-button").addEventListener("click", incrementQuantity);
  document.getElementById("minus-button").addEventListener("click", decrementQuantity);
});

function updateSelectedColor(selectElement) {
  const selectedColor = selectElement.value;
  const selectedColorInput = document.getElementById("selectedColor");
  selectedColorInput.value = selectedColor;
}

function updateSelectedSize(selectElement) {
  const selectedSize = selectElement.value;
  const selectedSizeInput = document.getElementById("selectedSize");
  selectedSizeInput.value = selectedSize;
}

function changeImage(productId, imageSrc, zoomLevel) {
  var productImage = document.getElementById(productId);
  var imageElement = productImage.getElementsByTagName("img")[0]; // Explicitly target <img>
  imageElement.src = imageSrc; 
  imageElement.style.transform = `scale(${zoomLevel})`; 
}

