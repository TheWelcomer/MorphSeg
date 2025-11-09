<script>
    let chefs = [["Cynthia", "/assets/Sprite-Cynthia_Chef.gif"], ["Nathan", "/assets/Sprite-Nathan_Chef.gif"], ["Taoran", "/assets/Sprite-Taoran_Chef.gif"], ["Donnie", "/assets/Sprite-Donny_Chef.gif"], ["Alexis", "/assets/Sprite-Alexis_Chef.gif"]];
    
    let started = $state(false) 

    function startCooking() {
        started = true
    }
</script>

<style>
    @import "style.css";
    #starting-board {
        background-image: url("/assets/Sprite-cuttingboard.png");
        align-items: center;
        justify-content: center;
        display: flex;
        position: fixed;
        background-repeat: no-repeat;
        background-size: contain;
        background-position: left center;
        margin: none;
        z-index: 20;
        width: min(80%, 80vh * 463 / 279);
        margin: 2.5% 18% 5% auto;
        aspect-ratio: calc(463 / 279);
        left: 50%;
        transform: translate(-50%, 0);
        display: grid;
    }
    #startid {
        background-color: transparent;
        height: 100%;
        width: 100%;
    }
    .chef {
        image-rendering: pixelated;
        width: 6vmax;
    }
    #chefs {
      padding: 17% 0 10% 0;
      position: fixed;
      left: 45%;
      transform: translate(-50%, 0);
    }
    #declaration {
        text-align: center;
        margin: 0 12% 0 0;
        font-size: 10vh;
        color: #523629;
    }
    #instruction {
        text-align: center;
        margin: 0% 12% 5% 0;
        font-size: 4vh;
        color: #322013;
        animation: 1s linear infinite normal blink;
    }
    @keyframes blink {
        from {
            visibility: visible;
        }
        to {
            visibility: hidden;
        }
    }
</style>

{#if !started}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div id="starting-board" onclick={startCooking}>
        <div id="declaration">MORPHOLOGICAL SEGMENTATION!</div>
        <div id=chefs>
            {#each chefs as chef, order}
                <img class="chef" src={chef[1]} alt={chef[0]} style="left:{35+order*5}vw">
            {/each}
        </div>
        <div id="instruction">click here to start</div>
    </div>
{/if}
