
<style media="screen">

  .appMenu ul{
    list-style: none;
  }
  .appMenu ul>li{
    float: left;
    /*background: #f1f1f1;*/
    margin: 0;
    height: 45px;
    line-height: 45px;
    display: inline-block;
    padding: 0 20px;
    cursor: pointer;
  }
  .appMenu ul>li>a{
    font-size: 1rem;
    font-weight: 400;
    color: #333;
    text-transform: uppercase;
  }
  .subMenuBg{
    position: absolute;
    top: 45px;
    left: 0;
    right: 0;
    background: #f9f9f9;
    min-height: 100px;
    border-bottom: 1px #e5e5e5 solid;
    z-index: 10000;
  }
  .nav-header-wrapper{
    position: relative;
    height: 45px;
    margin: 0;
    padding: 0;
    border: 0;
  }
  .appMenu{
    position: absolute;
    width: 100%;
    top: 0;
    z-index: 1210;
  }






  .nav-menu{
    position: relative;
    width: 100%;
    height: 45px;
    top: 0;
    left: 0;
    z-index: 1011;
    border-bottom: 1px #e5e5e5 solid;
  }
  .nav-menu-wrapper-container{
    background-color: #fff;
    overflow-y: scroll;
    overflow-x: hidden;
    position: absolute;
    top: 45px;
    transition: all .4s ease!important;
    z-index: 1012;
    opacity: 0;
    margin-right: auto;
    margin-left: auto;
    padding-right: 0;
    padding-left: 0;
    width: 100%;
    left: 0;
    scrollbar-width: none;
    -ms-overflow-style: none;
    box-shadow: 0 16px 16px rgb(0 0 0 / 10%);
  }
  .-sub-container{
    display: none;
    background: transparent;
  }
  .-menu-item:hover, .-has-sub-menu.-hover{
    border-bottom: solid 2px #c1b186;
  }
  .nav-menu-overlay{
    position: absolute;
    z-index: 1000;
    transition: all .6s ease;
    opacity: 0;
    height: 100vh;
    width: 100%;
    top: 45px;
    visibility: hidden;
  }
  .nav-menu-overlay.-open{
    opacity: 1;
    visibility: visible;
    /*background: rgba( 0, 0, 0, 0.5);*/
  }



  /* Mobile */

  .mobile-menu{
    display: none;
    position: fixed;;
    top: 0px;
    width: 100%;
    height: 45px;
    z-index: 1005;
    border-bottom: solid 1px #e5e5e5;
  }
  .mobile-menu .mobile-logo{
    float: left;
    display: block;
    width: 100%;
    text-align: center;
    padding: 10px 10px;
    line-height: 31px;
  }
  .mobile-menu .mobile-logo a{
    padding: 0;
  }
  .mobile-menu .mobile-logo i{
    font-size: 20px;
  }
  .mobile-menu .left{
    position: absolute;
    left: 0;
    top: 0;
  }
  .mobile-menu .right{
    position: absolute;
    right: 0;
    top: 0;
  }
  .mobile-menu button, .mobile-menu a{
    background: transparent;
    border: none;
    color: #000;
    padding: 10px;
    font-size: 15px;
    line-height: 1;
    height: 45px;
  }
  .mobile-menu button:focus, .mobile-menu a:focus{
    outline: none;
  }



  .appMenu.-mobile{
    background: #fff;
    left: -100%;
    transition: all .3s ease;
    position: fixed;
    top: 45px;
    overflow: auto;
  }
  .appMenu.-mobile .nav-menu{
    height: 100vh;
    overflow-y: scroll;
    border-bottom-color: transparent;
  }
  .appMenu.-mobile ul>li{
    float: none;
    display: block;
    position: relative;
    border-bottom: solid 1px #e5e5e5;
  }
  .appMenu.-mobile ul>li.-has-sub-menu:after{
    right: 15px;
    top: 13px;
    position: absolute;
    height: 16px;
    width: 16px;
    display: block;
    content: "";
    line-height:20px;
    vertical-align:top;
    background:url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiI+PHBhdGggZmlsbC1vcGFjaXR5PSIuODUiIGZpbGwtcnVsZT0iZXZlbm9kZCIgZD0iTTMgNi4xMDVhMS4wMDIgMS4wMDIgMCAwMTEuNDE2IDBMOCA5LjY4NGwzLjU4NC0zLjU3OWExLjAwMiAxLjAwMiAwIDAxMS40MTYgMGwtNC42NDYgNC42NGEuNTAxLjUwMSAwIDAxLS43MDggMEwzIDYuMTA0eiIvPjwvc3ZnPg==)
  }
  .appMenu.-mobile-open{
    left: 0;
  }
  .mobile-menu-extra-content{
    display: none;
    position: relative;
    padding: 0px 10px;
    margin-top: 0px;
    height: auto;
    padding-top: 7px;
  }
  .-mobile-sub-container{
    display: none;
  }

  .mobile-locator{
    line-height: 1;
    padding: 10px;
    display: inline-block;
  }
  .mobile-locator .location-selector{
    min-width: 50px;
  }
  .mobile-locator .location-selector>span{
    display: none;
  }
  .menu-user-links{
    display: inline-block;
  }
  .menu-user-links .top-user-link{
    line-height: 1;
    padding: 10px;
    display: inline-block;
  }
  .menu-user-links .top-user-link span.label{
    display: inline-block;
  }


  @media (min-width: 791px){
    .nav-menu.center-menu{
      text-align: center;
    }
    .nav-menu.center-menu ul{
      display: inline-block;
    }
    .-menu-item.-has-sub-menu{
      padding-right: 30px;
      position: relative;
    }
    .-menu-item.-has-sub-menu::after{
      position: absolute;
      right: 12px;
      top: 14px;
      height: 16px;
      width: 16px;
      display: block;
      content: "";
      line-height: 20px;
      vertical-align: top;
      background:url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiI+PHBhdGggZmlsbC1vcGFjaXR5PSIuODUiIGZpbGwtcnVsZT0iZXZlbm9kZCIgZD0iTTMgNi4xMDVhMS4wMDIgMS4wMDIgMCAwMTEuNDE2IDBMOCA5LjY4NGwzLjU4NC0zLjU3OWExLjAwMiAxLjAwMiAwIDAxMS40MTYgMGwtNC42NDYgNC42NGEuNTAxLjUwMSAwIDAxLS43MDggMEwzIDYuMTA0eiIvPjwvc3ZnPg==)
    }
    .nav-header-wrapper.-fixed{
      transition: top 500ms, bottom 500ms;
      position: fixed;
      width: 100%;
      z-index: 1050;
      background: #fff;
    }
  }

  @media (max-width: 790px){
    .top-nav{
      position: fixed;
      z-index: 1000;
      width: 100%;
    }
    .mobile-menu, .mobile-menu-extra-content{
      display: block;
    }
    .mobile-menu{
      background: #fff;
    }
    .nav-menu-overlay{
      display: none;
    }
    .nav-header-wrapper{
      height: 45px;
    }
    .-mobile-sub-container.-open{
      display: block;
    }
    .appMenu.-mobile ul>li{
      height: auto;
    }
  }


</style>





<div class="nav-header-wrapper">

  <div class="mobile-menu">
    <div class="left">
      <button type="button" name="button" data-menu="mobile"> <i class="ti-menu"></i> </button>
    </div>
    <div class="mobile-logo">
      <a href="{$urls.pages.index}">
        <i class="ti-glab" style="color:#c1b186"></i>
        <i class="ti-packaging" style="color:#767676"></i>
      </a>
    </div>
    <div class="right">
      <a href="{$urls.pages.my_account}"> <i class="ti-user"></i> </a>
      <button type="button" name="button" data-card="preview"> <i class="ti-bag"></i><span class="cart-count"></span> </button>
    </div>
  </div>

  <div class="appMenu">
    <nav class="nav-menu center-menu">
      <ul>
        
        <li class="-menu-item -has-sub-menu" data-target="1">
          <a href="#">Shopping Bags</a>
          <div class="-mobile-sub-container" mobile-data="target-1"></div>
        </li>

        <li class="-menu-item -has-sub-menu" data-target="2">
          <a href="#">Boxes</a>
          <div class="-mobile-sub-container" mobile-data="target-2"></div>
        </li>

        <li class="-menu-item -has-sub-menu">
          <a href="#"> Accessories </a>
          <div class="-mobile-sub-container"></div>
        </li>

        <li class="-menu-item">
          <a href="#"> Mothers day </a>
        </li>
      </ul>

      <div class="mobile-menu-extra-content">

        <div class="menu-user-links" mobile-data="top-user-links"></div>
        <div class="mobile-locator" mobile-data="mobile-locator"></div>
      </div>
    </nav>
    <div class="nav-menu-wrapper-container">
        <div class="-sub-container -target-1" menu-mobile-target="target-1">
          <div class="container">
            <div class="row">
              <div class="col-md-3">
                <img src="https://dji-official-fe.djicdn.com/cms/uploads/e25101f5b918ca19fedbf8ae5c308bcb.jpg" style="width:100%" alt="">
              </div>
              <div class="col-md-3">
                <img src="https://dji-official-fe.djicdn.com/cms/uploads/e25101f5b918ca19fedbf8ae5c308bcb.jpg" style="width:100%" alt="">
              </div>
              <div class="col-md-3">
                <img src="https://dji-official-fe.djicdn.com/cms/uploads/e25101f5b918ca19fedbf8ae5c308bcb.jpg" style="width:100%" alt="">
              </div>
              <div class="col-md-3">
                <img src="https://dji-official-fe.djicdn.com/cms/uploads/e25101f5b918ca19fedbf8ae5c308bcb.jpg" style="width:100%" alt="">
              </div>
            </div>
          </div>
        </div>
        <div class="-sub-container -target-2" menu-mobile-target="target-2">
          <div class="container">
            <div class="row">
              <div class="col-md-3">
                <img src="https://stormsend1.djicdn.com/tpc/uploads/spu_bundle/cover/2bd7efa3df45777c0200828cfac04b09@large.png" style="width:100%" alt="">
              </div>
              <div class="col-md-3">
                <img src="https://stormsend1.djicdn.com/tpc/uploads/sku/cover/e8a7681d245a01848049e638b3fc1819@xlarge.png" style="width:100%" alt="">
              </div>
              <div class="col-md-3">
                <img src="https://stormsend1.djicdn.com/tpc/uploads/sku/cover/8b5c1d9b-eba7-4cb1-ab6d-40dd6415b7d7@large.png" style="width:100%" alt="">
              </div>
              <div class="col-md-3">
                <img src="https://stormsend1.djicdn.com/tpc/uploads/spu/cover/8b8cf6eef92b612a35c5b57b2863fa00@large.png" style="width:100%" alt="">
              </div>
            </div>
          </div>
        </div>
      </div>
  </div>
  <div class="nav-menu-overlay"></div>

</div>







