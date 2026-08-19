const GITHUB_URL = "https://github.com/Joey766/ZhiyueAI";
const PRODUCT_WEBSITE_URL = "https://joey766.github.io/ZhiyueAI/";
// Set this to the separately deployed Streamlit product URL during release.
// Leave blank in source control: the landing page will show the deployment note.
const PUBLIC_APP_URL = "";
document.querySelectorAll("#github-link, #github-hero-link").forEach((link) => { link.href = GITHUB_URL; });
const appLink = document.querySelector("#app-link");
if (PUBLIC_APP_URL) {
  appLink.href = PUBLIC_APP_URL;
  appLink.target = "_blank";
  appLink.rel = "noreferrer";
}
