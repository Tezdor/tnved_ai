import {
latestResults
}
from "./state.js";



export async function downloadPDF(){


if(!latestResults)
return;



const response =
await fetch(
"/api/download-pdf/",
{


method:"POST",


headers:{

"Content-Type":
"application/json"

},


body:
JSON.stringify(
latestResults
)


});



const blob =
await response.blob();



const url =
window.URL.createObjectURL(
blob
);



const a =
document.createElement(
"a"
);



a.href=url;


a.download=
"tnved_result.pdf";



document.body.appendChild(a);


a.click();


a.remove();


}