# Setting Up Ad Serving for MathTutor

This guide will walk you through the process of setting up ad serving for your MathTutor application to generate revenue.

## Ad Serving Overview

MathTutor is configured to serve ads from two major ad networks:
1. **Google AdSense** - The primary ad network that serves text, display, and native ads
2. **Facebook Audience Network** - An additional ad network that can be used to maximize revenue

By serving ads on your MathTutor application, you can generate passive income based on impressions and clicks from your users.

## Prerequisites

- A Google account
- A live website with a domain (AdSense doesn't work with localhost)
- Your website must comply with [Google AdSense program policies](https://support.google.com/adsense/answer/48182)

## Step 1: Create a Google AdSense Account

1. Go to [Google AdSense](https://www.google.com/adsense)
2. Sign in with your Google account
3. Complete the application form with your website details
4. Accept the AdSense terms and conditions
5. Add the verification code to your website (see Step 2)
6. Wait for Google to review and approve your application (usually takes 1-3 days)

## Step 2: Add the AdSense Verification Code

During the application process, Google will provide you with a verification code. This code needs to be added to your website to verify ownership.

The MathTutor application is already set up to include the AdSense code in the base template. You just need to:

1. Add your AdSense client ID to the `.env` file:

```
GOOGLE_ADSENSE_CLIENT_ID=ca-pub-XXXXXXXXXXXXXXXX
```

2. Restart your application for the changes to take effect.

## Step 3: Create Ad Units

Once your AdSense account is approved:

1. Log in to your [AdSense account](https://www.google.com/adsense)
2. Go to "Ads" > "By ad unit"
3. Click "Create new ad unit"
4. Choose the ad type (display, in-feed, in-article, etc.)
5. Configure the ad settings (size, style, etc.)
6. Save the ad unit

You'll receive an ad unit ID for each ad unit you create. Add these IDs to your `.env` file:

```
GOOGLE_ADSENSE_DEFAULT_SLOT=XXXXXXXXXX
GOOGLE_ADSENSE_SIDEBAR_SLOT=XXXXXXXXXX
GOOGLE_ADSENSE_NATIVE_SLOT=XXXXXXXXXX
```

## Step 4: Ad Placement in MathTutor

The MathTutor application already includes ad components in various templates:

- Sidebar ads on the homepage, subscription page, and past worksheets page
- Native ads on the children management page
- Horizontal ads in the footer of all pages

These ad placements are implemented using Jinja2 macros in the `components/ads.html` file:

```jinja
{% from "components/ads.html" import google_ad, sidebar_ad, native_ad %}

{# For a sidebar ad #}
{{ sidebar_ad() }}

{# For a native ad #}
{{ native_ad() }}

{# For a custom ad with specific slot ID and format #}
{{ google_ad('YOUR_SLOT_ID', 'horizontal') }}
```

## Step 5: Facebook Audience Network (Optional)

To maximize your ad revenue, you can also set up Facebook Audience Network:

1. Create a Facebook Developer account at [developers.facebook.com](https://developers.facebook.com/)
2. Create a new app for your website
3. Add the Audience Network product to your app
4. Create ad placements and get your placement IDs
5. Add your Facebook App ID and placement ID to the `.env` file:

```
FACEBOOK_AD_APP_ID=XXXXXXXXXX
FACEBOOK_AD_DEFAULT_PLACEMENT=XXXXXXXXXX
```

## Step 6: Testing Your Ads

To test if your ads are displaying correctly:

1. Deploy your application to a live domain
2. Visit your website and check if the ads are displaying
3. Use the [AdSense Preview Tool](https://support.google.com/adsense/answer/10762946) to preview how ads will appear on your site

Note: You won't see real ads during testing. Instead, you'll see test ads or blank spaces.

## Step 7: Optimizing Ad Revenue

To maximize your ad revenue:

1. **Placement Optimization**: Test different ad positions to find the best-performing locations
2. **Ad Size Optimization**: Try different ad sizes to see which ones generate the most revenue
3. **Ad Density**: Balance the number of ads with user experience (too many ads can drive users away)
4. **Content Quality**: Create high-quality content to attract more users and increase engagement
5. **Mobile Optimization**: Ensure your ads display properly on mobile devices

## Monitoring Performance

Once your ads are live:

1. Log in to your AdSense account
2. Go to the "Home" tab to see an overview of your earnings
3. Use the "Reports" tab for detailed performance metrics
4. Monitor key metrics like RPM (Revenue per 1000 impressions), CTR (Click-Through Rate), and CPC (Cost per Click)

## Troubleshooting

If your ads aren't displaying:

1. Check that your AdSense account is approved
2. Verify that your client ID and ad slot IDs are correct in the `.env` file
3. Make sure the ad code is properly included in your templates
4. Check the browser console for any JavaScript errors
5. Ensure you're not blocking ads with an ad blocker

## Additional Resources

- [Google AdSense Help Center](https://support.google.com/adsense)
- [AdSense Program Policies](https://support.google.com/adsense/answer/48182)
- [Ad Placement Policies](https://support.google.com/adsense/answer/1346295)
- [Facebook Audience Network Documentation](https://developers.facebook.com/docs/audience-network) 